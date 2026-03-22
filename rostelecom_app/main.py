import flet as ft
import qrcode
import base64
from io import BytesIO
import time
import hmac
import hashlib
import threading

# --- КОНСТАНТЫ ---
RT_PURPLE = "#7B47E0"
RT_ORANGE = "#FF4F12"
RT_BG = "#F2F2F2"
SECRET_KEY = "RTK_INTERNAL_KEY_2026"

# База данных пользователей
users_db = {
    "admin": {"name": "Иван Иванов", "pos": "Системный администратор", "pass": "admin", "role": "admin"},
    "user1": {"name": "Петр Петров", "pos": "Инженер связи", "pass": "1234", "role": "user"}
}

def main(page: ft.Page):
    page.title = "РТК: Точка входа"
    page.theme_mode = ft.ThemeMode.LIGHT
    
    page.window.width = 400
    page.window.height = 800
    page.window.resizable = False
    
    page.padding = 0
    page.bgcolor = RT_BG

    state = {"user": None, "username": None, "timer_id": 0}

    # Логика проверки QR-кода
    def verify_qr(qr_text):
        try:
            parts = qr_text.strip().split("|")
            if len(parts) != 3: return False, "Неверный формат кода"
            u, ts, sign = parts
            if int(time.time()) - int(ts) > 300: return False, "Время действия пропуска истекло"
            expected = hmac.new(SECRET_KEY.encode(), f"{u}|{ts}".encode(), hashlib.sha256).hexdigest()[:10]
            if sign == expected: return True, users_db.get(u)
            return False, "Поддельный QR-код"
        except: return False, "Ошибка чтения данных"

    # --- ЭКРАН 1: РЕЖИМ ТУРНИКЕТА (СКАНЕР) ---
    def show_scanner(e=None):
        page.clean()
        inp = ft.TextField(label="Вставьте сюда текст из QR-кода", border_radius=10, bgcolor="white", width=300)
        result_text = ft.Text("Ожидание сканирования...", size=16, weight="bold", color="grey", text_align=ft.TextAlign.CENTER)
        
        def check(e):
            ok, info = verify_qr(inp.value)
            if ok:
                result_text.value = f"ДОСТУП РАЗРЕШЕН\nСотрудник: {info['name']}\nДолжность: {info['pos']}"
                result_text.color = "green"
            else:
                result_text.value = f"В ДОСТУПЕ ОТКАЗАНО\nПричина: {info}"
                result_text.color = "red"
            page.update()
            
        page.add(
            ft.Container(
                bgcolor=RT_PURPLE, padding=ft.padding.only(20, 40, 20, 20),
                content=ft.Row([
                    ft.Text("СКУД: Турникет", color="white", size=18, weight="bold"),
                    ft.IconButton(ft.Icons.ARROW_BACK, icon_color="white", on_click=lambda _: show_login())
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ),
            ft.Container(padding=20, content=ft.Column([
                ft.Icon(ft.Icons.NFC, size=80, color=RT_PURPLE),
                ft.Text("Режим эмуляции сканера", size=18, weight="bold"),
                inp, 
                ft.ElevatedButton("ЭМУЛИРОВАТЬ СКАНИРОВАНИЕ", on_click=check, bgcolor=RT_PURPLE, color="white", width=300),
                ft.Container(height=20),
                result_text,
                ft.Container(height=40),
                ft.TextButton("Вернуться на главный экран", on_click=lambda _: show_login())
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER))
        )

    # --- ЭКРАН 2: ПАНЕЛЬ АДМИНИСТРАТОРА ---
    def show_admin_panel():
        page.clean()
        f_n = ft.TextField(label="ФИО сотрудника", width=300, bgcolor="white")
        f_p = ft.TextField(label="Должность", width=300, bgcolor="white")
        f_u = ft.TextField(label="Придумайте логин", width=300, bgcolor="white")
        f_w = ft.TextField(label="Придумайте пароль", width=300, bgcolor="white")
        msg = ft.Text("", size=14, weight="bold", text_align=ft.TextAlign.CENTER)

        def save(e):
            if not all([f_n.value, f_p.value, f_u.value, f_w.value]):
                msg.value = "Пожалуйста, заполните все поля!"
                msg.color = "red"
            elif f_u.value in users_db:
                msg.value = "Сотрудник с таким логином уже существует!"
                msg.color = "red"
            else:
                users_db[f_u.value] = {"name": f_n.value, "pos": f_p.value, "pass": f_w.value, "role": "user"}
                msg.value = f"Успех!\nСотрудник {f_n.value} добавлен."
                msg.color = "green"
                f_n.value = f_p.value = f_u.value = f_w.value = "" # Очистка полей
            page.update()

        page.add(
            ft.Container(
                bgcolor=RT_PURPLE, padding=ft.padding.only(20, 40, 20, 20),
                content=ft.Row([
                    ft.Text("Панель Администратора", color="white", size=18, weight="bold"),
                    ft.IconButton(ft.Icons.LOGOUT, icon_color="white", on_click=lambda _: show_login())
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ),
            ft.Container(padding=20, content=ft.Column([
                ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS, size=60, color=RT_ORANGE),
                ft.Text("Создание учетной записи", size=20, weight="bold", color=RT_PURPLE),
                ft.Container(height=10),
                f_n, f_p, f_u, f_w, 
                ft.ElevatedButton("ЗАРЕГИСТРИРОВАТЬ СОТРУДНИКА", on_click=save, bgcolor=RT_ORANGE, color="white", width=300, height=45),
                msg
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15))
        )

    # --- ЭКРАН 3: ПРИЛОЖЕНИЕ СОТРУДНИКА (ГЕНЕРАЦИЯ QR) ---
    def show_employee_panel():
        page.clean()
        u = state["user"]
        
        # ИСПРАВЛЕНИЕ: Используем src вместо src_base64
        qr_img = ft.Image(src="", width=200, height=200, visible=False)
        
        timer = ft.Text("", size=16, weight="bold", color=RT_ORANGE)
        raw_t = ft.Text("", size=10, color="grey", selectable=True)

        def gen(e):
            state["timer_id"] += 1; cur = state["timer_id"]
            ts = int(time.time()); msg = f"{state['username']}|{ts}"
            sign = hmac.new(SECRET_KEY.encode(), msg.encode(), hashlib.sha256).hexdigest()[:10]
            val = f"{msg}|{sign}"
            
            # Генерация картинки QR и перевод в base64
            q = qrcode.make(val); b = BytesIO(); q.save(b, format="PNG")
            b64_str = base64.b64encode(b.getvalue()).decode()
            
            # ИСПРАВЛЕНИЕ: Передаем картинку в стандартный src как Data URI
            qr_img.src = f"data:image/png;base64,{b64_str}"
            qr_img.visible = True
            
            raw_t.value = val; page.update()
            
            # Таймер на 5 минут
            def clock():
                for i in range(300, -1, -1):
                    if state["timer_id"] != cur: return
                    timer.value = f"Пропуск активен: {i} сек"; page.update(); time.sleep(1)
                timer.value = "Срок действия пропуска истек"
                qr_img.visible = False
                raw_t.value = ""
                page.update()
                
            threading.Thread(target=clock, daemon=True).start()

        page.add(
            ft.Container(bgcolor=RT_PURPLE, padding=ft.padding.only(20, 40, 20, 20), content=ft.Row([
                ft.Column([ft.Text("Профиль сотрудника", color="white70", size=12), ft.Text(u["name"], color="white", size=18, weight="bold")]),
                ft.IconButton(ft.Icons.LOGOUT, icon_color="white", on_click=lambda _: show_login())
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)),
            ft.Container(padding=20, content=ft.Column([
                ft.Container(padding=15, bgcolor="white", border_radius=10, content=ft.Row([ft.Icon(ft.Icons.BADGE, color=RT_PURPLE), ft.Text(u["pos"], expand=True)])),
                ft.Container(padding=20, bgcolor="white", border_radius=20, alignment=ft.Alignment(0, 0), content=ft.Column([
                    qr_img, 
                    ft.Icon(ft.Icons.QR_CODE_2, size=100, color="#DDD", visible=not qr_img.visible),
                    timer, 
                    ft.Text("Скрытый код для тестов (скопируйте):", size=10, color="#DDD", visible=True),
                    raw_t
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)),
                ft.ElevatedButton("СГЕНЕРИРОВАТЬ ПРОПУСК", on_click=gen, bgcolor=RT_ORANGE, color="white", width=300, height=50)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20))
        )

    # --- ЭКРАН 4: ОКНО ВХОДА ---
    def show_login():
        page.clean()
        u_in = ft.TextField(label="Логин", value="admin", width=280)
        p_in = ft.TextField(label="Пароль", password=True, value="admin", width=280)
        err = ft.Text("", color="red", visible=False)

        def login(e):
            if u_in.value in users_db and users_db[u_in.value]["pass"] == p_in.value:
                state["user"] = users_db[u_in.value]
                state["username"] = u_in.value
                
                # РОУТИНГ (Разделение прав)
                if state["user"]["role"] == "admin":
                    show_admin_panel()
                else:
                    show_employee_panel()
            else:
                err.value = "Неверный логин или пароль"; err.visible = True; page.update()

        page.add(
            ft.Container(
                expand=True,
                gradient=ft.LinearGradient(
                    colors=["#7B47E0", "#4B2691"], 
                    begin=ft.Alignment(0, -1),
                    end=ft.Alignment(0, 1)
                ),
                content=ft.Column([
                    ft.Container(height=60),
                    ft.Text("РОСТЕЛЕКОМ", color="white", size=32, weight="bold"),
                    ft.Text("ТОЧКА ВХОДА", color="white70", size=16),
                    ft.Container(height=20),
                    ft.Container(bgcolor="white", padding=30, border_radius=20, content=ft.Column([
                        u_in, p_in, err,
                        ft.ElevatedButton("ВОЙТИ", on_click=login, bgcolor=RT_ORANGE, color="white", height=50, width=220)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)),
                    ft.Container(height=30),
                    ft.TextButton("РЕЖИМ ТУРНИКЕТА (СКУД)", on_click=show_scanner, style=ft.ButtonStyle(color="white60"))
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )
        )

    # Запускаем начальный экран
    show_login()

if __name__ == "__main__":
    ft.run(main)
