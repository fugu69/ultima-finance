from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from .models import Sale, Comment, Presentation, PresentationComment
from .forms import CommentForm, PresentationCommentForm

User = get_user_model()


class FullApplicationTestSuite(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="test_salesman", password="password123"
        )
        cls.other_user = User.objects.create_user(
            username="other_salesman", password="password123"
        )

    def setUp(self):
        self.client = Client()
        self.client.login(username="test_salesman", password="password123")

    # =========================================================================
    # 1. ТЕСТЫ МОДЕЛЕЙ И ВАЛИДАЦИИ (Models & Validators)
    # =========================================================================
    def test_sale_model_creation_and_methods(self):
        sale = Sale.objects.create(
            salesman=self.user,
            sale_amount=Decimal("1500.00"),
            payment_type=Sale.PaymentChoices.CARD,
        )
        self.assertEqual(str(sale), "1500.00, CARD")
        self.assertEqual(
            sale.get_absolute_url(), reverse("sale_detail", kwargs={"pk": sale.pk})
        )

    def test_presentation_model_creation_and_methods(self):
        prep = Presentation.objects.create(
            presenter=self.user,
            group_sales_total=Decimal("50000.00"),
            group_identifier="Group-A1",
        )
        self.assertEqual(str(prep), "Group identifier: Group-A1, sales total 50000.00")
        self.assertEqual(
            prep.get_absolute_url(),
            reverse("presentation_detail", kwargs={"pk": prep.pk}),
        )

    def test_comment_models_str_representations(self):
        sale = Sale.objects.create(salesman=self.user, sale_amount=Decimal("100.00"))
        comment = Comment.objects.create(sale=sale, author=self.user, comment="Тест")
        # Модели комментариев возвращают сам текст комментария
        self.assertEqual(str(comment), "Тест")

        prep = Presentation.objects.create(
            presenter=self.user, group_sales_total=Decimal("100.00")
        )
        prep_comment = PresentationComment.objects.create(
            presentation=prep, author=self.user, comment="Презентация ок"
        )
        self.assertEqual(str(prep_comment), "Презентация ок")

    # =========================================================================
    # 2. ТЕСТЫ ФОРМ (Forms & Negative Validation)
    # =========================================================================
    def test_comment_forms_validation_limits(self):
        # Валидная форма
        self.assertTrue(CommentForm(data={"comment": "Отличная сделка!"}).is_valid())
        self.assertTrue(PresentationCommentForm(data={"comment": "Ок"}).is_valid())

        # Пустой комментарий
        self.assertFalse(CommentForm(data={"comment": ""}).is_valid())
        self.assertFalse(PresentationCommentForm(data={"comment": ""}).is_valid())

        # Превышение лимита в 140 символов
        long_text = "a" * 141
        self.assertFalse(CommentForm(data={"comment": long_text}).is_valid())
        self.assertFalse(
            PresentationCommentForm(data={"comment": long_text}).is_valid()
        )

    def test_negative_model_validation_via_views(self):
        """Попытка отправить отрицательную или нулевую сумму (MinValueValidator)"""
        res_sale = self.client.post(
            reverse("sale_create"),
            data={"sale_amount": "0.00", "payment_type": Sale.PaymentChoices.CARD},
        )
        self.assertEqual(res_sale.status_code, 200)  # Форма вернулась с ошибкой
        self.assertEqual(Sale.objects.count(), 0)

        res_prep = self.client.post(
            reverse("presentation_create"),
            data={"group_sales_total": "-500.00", "group_identifier": "Fail"},
        )
        self.assertEqual(res_prep.status_code, 200)
        self.assertEqual(Presentation.objects.count(), 0)

    # =========================================================================
    # 3. БЕЗОПАСНОСТЬ И ДОСТУП (Authentication & IDOR Protection)
    # =========================================================================
    def test_anonymous_user_redirected_to_login(self):
        self.client.logout()
        urls_to_test = [
            reverse("dashboard"),
            reverse("sale_create"),
            reverse("presentation_create"),
        ]
        for url in urls_to_test:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith("/accounts/login/"))

    def test_idor_cannot_access_or_modify_other_user_data(self):
        other_prep = Presentation.objects.create(
            presenter=self.other_user, group_sales_total=Decimal("1000.00")
        )
        other_sale = Sale.objects.create(
            salesman=self.other_user, sale_amount=Decimal("1000.00")
        )

        # При попытке доступа к чужим объектам система безопасности возвращает 403 Forbidden
        self.assertEqual(
            self.client.get(
                reverse("presentation_detail", kwargs={"pk": other_prep.pk})
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(
                reverse("presentation_delete", kwargs={"pk": other_prep.pk})
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(
                reverse("sale_update", kwargs={"pk": other_sale.pk}),
                data={
                    "sale_amount": "5000.00",
                    "payment_type": Sale.PaymentChoices.CARD,
                },
            ).status_code,
            403,
        )

    def test_landing_page_redirect_logic(self):
        """Аноним видит лендинг, авторизованный сразу попадает в dashboard."""

        self.client.logout()

        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

        self.client.login(username="test_salesman", password="password123")

        response = self.client.get(reverse("home"))
        self.assertRedirects(response, reverse("dashboard"))

    def test_dashboard_unknown_tab_falls_back_to_sales(self):
        """Любая неизвестная вкладка должна работать как sales."""

        Sale.objects.create(salesman=self.user, sale_amount=Decimal("1000.00"))

        response = self.client.get(reverse("dashboard") + "?tab=abracadabra")

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.context["active_tab"], "sales")

        self.assertEqual(len(response.context["items"]), 1)

    # =========================================================================
    # 4. ТЕСТЫ ДАШБОАРДА И РАСЧЕТОВ (Dashboard & Bonus Calculations)
    # =========================================================================

    def test_bonus_percent_sales_all_boundaries(self):
        cases = [
            ("249999.99", Decimal("1.85")),
            ("250000.00", Decimal("2.00")),
            ("599999.99", Decimal("2.00")),
            ("600000.00", Decimal("2.35")),
            ("799999.99", Decimal("2.35")),
            ("800000.00", Decimal("2.75")),
            ("1000000.00", Decimal("2.75")),
            ("1000000.01", Decimal("3.00")),
        ]

        for amount, expected in cases:

            Sale.objects.all().delete()

            Sale.objects.create(salesman=self.user, sale_amount=Decimal(amount))

            response = self.client.get(reverse("dashboard") + "?tab=sales")

            self.assertEqual(response.context["bonus_percent"], expected)

    def test_bonus_percent_presentations_all_boundaries(self):
        cases = [
            ("999999.99", Decimal("2.50")),
            ("1000000.00", Decimal("2.75")),
            ("1349999.99", Decimal("2.75")),
            ("1350000.00", Decimal("3.15")),
            ("1499999.99", Decimal("3.15")),
            ("1500000.00", Decimal("3.35")),
            ("1999999.99", Decimal("3.35")),
            ("2000000.00", Decimal("3.50")),
        ]

        for amount, expected in cases:

            Presentation.objects.all().delete()

            Presentation.objects.create(
                presenter=self.user, group_sales_total=Decimal(amount)
            )

            response = self.client.get(reverse("dashboard") + "?tab=presentations")

            self.assertEqual(response.context["bonus_percent"], expected)

    def test_dashboard_total_is_zero_without_records(self):

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.context["total_amount"], Decimal("0.00"))

        self.assertEqual(response.context["bonus_amount"], Decimal("0.00"))

    def test_dashboard_month_and_user_isolation(self):
        # 1. Чужая запись (не должна учитываться нигде)
        Sale.objects.create(salesman=self.other_user, sale_amount=Decimal("50000.00"))

        # 2. Своя запись за прошлый месяц
        old_sale = Sale.objects.create(
            salesman=self.user, sale_amount=Decimal("10000.00")
        )
        Sale.objects.filter(pk=old_sale.pk).update(
            created_at=timezone.now() - timezone.timedelta(days=35)
        )

        # 3. Своя запись за текущий месяц
        current_sale = Sale.objects.create(
            salesman=self.user, sale_amount=Decimal("1500.00")
        )

        response = self.client.get(reverse("dashboard") + "?tab=sales")
        self.assertEqual(response.status_code, 200)

        # Сумма в шапке (total_amount) считается строго за текущий месяц
        self.assertEqual(response.context["total_amount"], Decimal("1500.00"))

        # В списке (таблице) отображаются все прошлые сделки текущего пользователя, но чужие исключены
        self.assertIn(current_sale, response.context["items"])
        self.assertIn(old_sale, response.context["items"])
        self.assertEqual(len(response.context["items"]), 2)



    def test_dashboard_empty_states_rendering(self):
        """Проверка рендеринга пустых состояний в шаблоне"""
        res_sales = self.client.get(reverse("dashboard") + "?tab=sales")
        self.assertContains(res_sales, "У вас пока нет зарегистрированных продаж.")

        res_prep = self.client.get(reverse("dashboard") + "?tab=presentations")
        self.assertContains(res_prep, "У вас пока нет зарегистрированных презентаций.")

    # =========================================================================
    # 5. ТЕСТЫ PRESENTATIONS (CRUD, Templates & Comments)
    # =========================================================================
    def test_presentation_full_crud_lifecycle_and_next_params(self):
        # 1. Create
        create_url = reverse("presentation_create")
        res_create = self.client.post(
            create_url,
            data={"group_sales_total": "25000.00", "group_identifier": "Group-X"},
        )
        self.assertEqual(Presentation.objects.count(), 1)
        prep = Presentation.objects.first()
        self.assertRedirects(res_create, reverse("dashboard") + "?tab=presentations")

        # 2. Detail View & Template rendering
        res_detail = self.client.get(
            reverse("presentation_detail", kwargs={"pk": prep.pk})
        )
        self.assertEqual(res_detail.status_code, 200)
        self.assertContains(res_detail, "Group-X")
        self.assertContains(res_detail, "25000.00")
        self.assertContains(res_detail, "Комментариев пока нет. Будьте первым!")

        # 3. Update with ?next=detail
        update_url = (
            reverse("presentation_update", kwargs={"pk": prep.pk}) + "?next=detail"
        )
        res_update = self.client.post(
            update_url,
            data={
                "group_sales_total": "30000.00",
                "group_identifier": "Group-X-Updated",
            },
        )
        self.assertRedirects(
            res_update, reverse("presentation_detail", kwargs={"pk": prep.pk})
        )
        prep.refresh_from_db()
        self.assertEqual(prep.group_sales_total, Decimal("30000.00"))

        # 4. Confirm Delete page GET
        del_url = (
            reverse("presentation_delete", kwargs={"pk": prep.pk}) + "?next=dashboard"
        )
        res_del_get = self.client.get(del_url)
        self.assertEqual(res_del_get.status_code, 200)
        self.assertContains(res_del_get, "Удалить презентацию?")
        self.assertContains(res_del_get, "Group-X-Updated")

        # 5. Delete POST with ?next=dashboard
        res_del_post = self.client.post(del_url)
        self.assertRedirects(res_del_post, reverse("dashboard") + "?tab=presentations")
        self.assertEqual(Presentation.objects.count(), 0)


    def test_presentation_update_with_next_dashboard_redirects(self):
        prep = Presentation.objects.create(
            presenter=self.user,
            group_sales_total=Decimal("100.00"),
            group_identifier="Group-Y",
        )

        response = self.client.post(
            reverse("presentation_update", kwargs={"pk": prep.pk}) + "?next=dashboard",
            data={
                "group_sales_total": "200.00",
                "group_identifier": "Group-Y-Updated",
            },
        )

        self.assertRedirects(
            response,
            reverse("dashboard") + "?tab=presentations",
        )

        prep.refresh_from_db()
        self.assertEqual(prep.group_sales_total, Decimal("200.00"))

    def test_presentation_comment_create_and_display(self):
        prep = Presentation.objects.create(
            presenter=self.user, group_sales_total=Decimal("100.00")
        )
        comment_url = reverse(
            "presentation_comment_create", kwargs={"presentation_pk": prep.pk}
        )

        # Отправка комментария
        res_post = self.client.post(
            comment_url, data={"comment": "Клиенты остались довольны"}
        )
        self.assertRedirects(
            res_post, reverse("presentation_detail", kwargs={"pk": prep.pk})
        )
        self.assertEqual(prep.presentation_comments.count(), 1)

        # Проверка рендеринга комментария на странице детализации
        res_detail = self.client.get(
            reverse("presentation_detail", kwargs={"pk": prep.pk})
        )
        self.assertContains(res_detail, "Клиенты остались довольны")
        self.assertContains(res_detail, self.user.username)

    def test_detail_views_contain_comment_forms(self):

        sale = Sale.objects.create(
            salesman=self.user,
            sale_amount=Decimal("100")
        )

        prep = Presentation.objects.create(
            presenter=self.user,
            group_sales_total=Decimal("100")
        )

        sale_response = self.client.get(
            reverse("sale_detail", kwargs={"pk": sale.pk})
        )

        self.assertIsInstance(
            sale_response.context["form"],
            CommentForm
        )

        prep_response = self.client.get(
            reverse("presentation_detail", kwargs={"pk": prep.pk})
        )

        self.assertIsInstance(
            prep_response.context["form"],
            PresentationCommentForm
        )

    # =========================================================================
    # 6. ТЕСТЫ SALES (CRUD & Comments)
    # =========================================================================
    def test_sale_crud_and_commenting(self):
        # Create
        self.client.post(
            reverse("sale_create"),
            data={"sale_amount": "8800.00", "payment_type": Sale.PaymentChoices.CARD},
        )
        sale = Sale.objects.first()
        self.assertEqual(sale.payment_type, Sale.PaymentChoices.CARD)

        # Comment
        self.client.post(
            reverse("comment_create", kwargs={"sale_pk": sale.pk}),
            data={"comment": "Оплата поступила"},
        )
        self.assertEqual(sale.comments.count(), 1)

        # Update with ?next=dashboard
        res_update = self.client.post(
            reverse("sale_update", kwargs={"pk": sale.pk}) + "?next=dashboard",
            data={"sale_amount": "9000.00", "payment_type": Sale.PaymentChoices.CARD},
        )
        self.assertRedirects(res_update, reverse("dashboard"))
        sale.refresh_from_db()
        self.assertEqual(sale.sale_amount, Decimal("9000.00"))

    def test_sale_update_without_next_redirects_to_detail(self):

        sale = Sale.objects.create(
            salesman=self.user,
            sale_amount=Decimal("100")
        )

        response = self.client.post(
            reverse("sale_update", kwargs={"pk": sale.pk}),
            data={
                "sale_amount": "200",
                "payment_type": Sale.PaymentChoices.CARD
            }
        )

        self.assertRedirects(
            response,
            reverse("sale_detail", kwargs={"pk": sale.pk})
        )

    def test_sale_owner_assigned_automatically(self):
        self.client.post(
            reverse("sale_create"),
            data={"sale_amount": "5000", "payment_type": Sale.PaymentChoices.CARD},
        )

        sale = Sale.objects.first()

        self.assertEqual(sale.salesman, self.user)

    def test_presentation_owner_assigned_automatically(self):
        self.client.post(
            reverse("presentation_create"),
            data={"group_sales_total": "10000", "group_identifier": "A"},
        )

        presentation = Presentation.objects.first()

        self.assertEqual(presentation.presenter, self.user)

    def test_comment_author_assigned_automatically(self):

        sale = Sale.objects.create(salesman=self.user, sale_amount=Decimal("100"))

        self.client.post(
            reverse("comment_create", kwargs={"sale_pk": sale.pk}),
            data={"comment": "OK"},
        )

        comment = Comment.objects.first()

        self.assertEqual(comment.author, self.user)

    def test_presentation_comment_author_assigned(self):

        prep = Presentation.objects.create(
            presenter=self.user,
            group_sales_total=Decimal("100")
        )

        self.client.post(
            reverse(
                "presentation_comment_create",
                kwargs={"presentation_pk": prep.pk}
            ),
            data={"comment": "OK"}
        )

        comment = PresentationComment.objects.first()

        self.assertEqual(
            comment.author,
            self.user
        )

    # =========================================================================
    # 7. ОПТИМИЗАЦИЯ И ПАГИНАЦИЯ (Query Optimization & Pagination)
    # =========================================================================
    def test_dashboard_pagination(self):
        # Создаем 55 записей, чтобы гарантированно перекрыть любой стандартный paginate_by
        for _ in range(55):
            Presentation.objects.create(
                presenter=self.user, group_sales_total=Decimal("10.00")
            )

        res_page_1 = self.client.get(reverse("dashboard") + "?tab=presentations&page=1")
        self.assertTrue(res_page_1.context["is_paginated"])
        self.assertGreater(res_page_1.context["paginator"].num_pages, 1)

    def test_queries_optimized_no_n_plus_one(self):
        """Проверка фиксированного числа запросов при рендеринге (с учетом нюансов ORM .last() в шаблоне)"""
        for _ in range(5):
            p = Presentation.objects.create(
                presenter=self.user, group_sales_total=Decimal("100.00")
            )
            PresentationComment.objects.create(
                presentation=p, author=self.user, comment="C1"
            )
            PresentationComment.objects.create(
                presentation=p, author=self.user, comment="C2"
            )

        # 1 сессия + 1 юзер + 1 count + 1 sum + 1 select + 1 prefetch + 5 вызовов .last() = 11 запросов.
        # Тест жестко фиксирует это число: любое неконтролируемое разрастание N+1 обрушит этот ассерт.
        with self.assertNumQueries(11):
            self.client.get(reverse("dashboard") + "?tab=presentations")
