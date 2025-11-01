# src/ui/home_ui.py
import tkinter as tk
from src.ui.review_ui import open_review_ui
from src.ui.history_ui import open_history_ui
from src.ui.random_ui import open_random_ui
from src.fetch import get_trending_products, get_product_info
import webbrowser


def open_home_ui():
    root = tk.Tk()
    root.title("🏠 URA – Universal Review Analyzer")
    root.geometry("1000x700")
    root.configure(bg="#f4f4f4")

    # ---- Title ----
    tk.Label(
        root,
        text="✨ Welcome to URA – Universal Review Analyzer ✨",
        font=("Arial", 20, "bold"),
        bg="#f4f4f4",
        fg="#222"
    ).pack(pady=20)

    # ---- Trending Products ----
    tk.Label(
        root,
        text="🔥 Trending Products",
        font=("Arial", 16, "bold"),
        bg="#f4f4f4",
        fg="#111"
    ).pack()

    trending_frame = tk.Frame(root, bg="#f4f4f4")
    trending_frame.pack(pady=20)

    trending = get_trending_products(limit=6)

    def display_product_card(idx=0, row=0, col=0):
        if idx >= len(trending):
            return

        product = trending[idx]
        info = get_product_info(product, max_images=1)

        card = tk.Frame(trending_frame, bg="white", relief="groove", bd=2)
        card.grid(row=row, column=col, padx=15, pady=15)

        # Image
        if info["images"]:
            img_label = tk.Label(card, image=info["images"][0], bg="white")
            img_label.image = info["images"][0]
            img_label.pack(padx=10, pady=10)

        # Name
        tk.Label(card, text=info["name"], font=("Arial", 12, "bold"), bg="white").pack(pady=5)

        # Buttons
        btn_frame = tk.Frame(card, bg="white")
        btn_frame.pack(pady=5)

        if info["buy_url"]:
            tk.Button(
                btn_frame, text="🛒 Buy", width=10,
                command=lambda u=info["buy_url"]: webbrowser.open(u)
            ).grid(row=0, column=0, padx=5)

        tk.Button(
            btn_frame, text="🔍 Analyze", width=10,
            command=lambda p=info["name"]: [root.destroy(), open_review_ui_with_product(p)]
        ).grid(row=0, column=1, padx=5)

        # Compute next row/col
        next_col = col + 1
        next_row = row
        if next_col >= 3:
            next_col = 0
            next_row += 1

        # Schedule next card with delay (animation effect)
        root.after(400, lambda: display_product_card(idx + 1, next_row, next_col))

    # Start showing trending products one by one
    display_product_card()

    # ---- Footer Buttons ----
    btn_frame = tk.Frame(root, bg="#f4f4f4")
    btn_frame.pack(pady=30)

    def styled_button(text, command, col):
        tk.Button(
            btn_frame,
            text=text,
            width=18,
            height=2,
            font=("Arial", 12),
            bg="#4CAF50",
            fg="white",
            activebackground="#45a049",
            relief="flat",
            command=command
        ).grid(row=0, column=col, padx=20)

    styled_button("📦 Product Review", lambda: open_review_ui(root), 0)
    styled_button("📜 History", lambda: open_history_ui(root), 1)
    styled_button("🎲 Random Product", lambda: open_random_ui(root), 2)

    # ---- Footer ----
    tk.Label(
        root,
        text="© 2025 URA – Universal Review Analyzer",
        font=("Arial", 10),
        bg="#f4f4f4",
        fg="#777"
    ).pack(side="bottom", pady=10)

    root.mainloop()


def open_review_ui_with_product(product_name):
    """
    Helper: open review UI with prefilled product name
    """
    import src.ui.review_ui as review_ui
    review_ui.open_review_ui(None, product_name=product_name)


if __name__ == "__main__":
    open_home_ui()
