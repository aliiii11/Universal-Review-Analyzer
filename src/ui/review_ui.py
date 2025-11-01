# src/ui/review_ui.py
import tkinter as tk
from tkinter import scrolledtext, messagebox
from src.analyze_reviews import analyze_reviews
from src.fetch import fetch_and_save_reviews, get_product_info
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import webbrowser


def open_review_ui(parent=None):
    if parent:
        parent.destroy()

    root = tk.Tk()
    root.title("📦 Product Review Analyzer")
    root.geometry("900x700")

    # ---------------- Product Input ----------------
    tk.Label(root, text="Enter Product Name:", font=("Arial", 12)).pack(pady=10)
    entry = tk.Entry(root, width=50, font=("Arial", 12))
    entry.pack(pady=5)

    status_label = tk.Label(root, text="", font=("Arial", 10), fg="blue")
    status_label.pack(pady=5)

    # ---------------- Product Info ----------------
    info_frame = tk.Frame(root)
    info_frame.pack(pady=10)

    image_frame = tk.Frame(info_frame)
    image_frame.grid(row=0, column=0, padx=20)

    product_label = tk.Label(info_frame, text="", font=("Arial", 14, "bold"))
    product_label.grid(row=0, column=1, sticky="w")

    buy_button = tk.Button(info_frame, text="🛒 Best Buy", state="disabled", font=("Arial", 12))
    buy_button.grid(row=1, column=1, sticky="w", pady=5)

    # ---------------- Verdict ----------------
    verdict_label = tk.Label(root, text="", font=("Arial", 14, "bold"), fg="green")
    verdict_label.pack(pady=10)

    # ---------------- Review Display ----------------
    review_frame = tk.Frame(root)
    review_frame.pack(fill="both", expand=True, padx=10, pady=10)

    scrollbar = tk.Scrollbar(review_frame)
    scrollbar.pack(side="right", fill="y")

    review_box = scrolledtext.ScrolledText(
        review_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set, height=15, width=100
    )
    review_box.pack(fill="both", expand=True)
    scrollbar.config(command=review_box.yview)

    # ---------------- Pros & Cons ----------------
    pros_label = tk.Label(root, text="Pros: ", font=("Arial", 12), fg="green")
    pros_label.pack(pady=5)
    cons_label = tk.Label(root, text="Cons: ", font=("Arial", 12), fg="red")
    cons_label.pack(pady=5)

    # ---------------- Chart Frame ----------------
    chart_frame = tk.Frame(root)
    chart_frame.pack(fill="both", expand=False, pady=10)

    # ---------------- Functions ----------------
    def analyze_product():
        product = entry.get().strip()
        if not product:
            messagebox.showwarning("Input Error", "⚠️ Please enter a product name!")
            return

        status_label.config(text="⏳ Fetching product info & reviews...")
        root.update_idletasks()

        # ---- Fetch product info (images + buy link) ----
        info = get_product_info(product, max_images=3)

        # Clear old product info
        for widget in image_frame.winfo_children():
            widget.destroy()
        product_label.config(text="")
        buy_button.config(state="disabled", command=None)

        if info["images"]:
            for i, img in enumerate(info["images"]):
                tk.Label(image_frame, image=img).grid(row=0, column=i, padx=5)
                image_frame.image = info["images"]  # keep reference

        product_label.config(text=info["name"])
        if info["buy_url"]:
            buy_button.config(state="normal", command=lambda: webbrowser.open(info["buy_url"]))

        # ---- Fetch & analyze reviews ----
        fetch_and_save_reviews(product)
        df = analyze_reviews()

        if df.empty:
            messagebox.showinfo("No Reviews", "No reviews found for this product.")
            return

        # Clear old analysis
        review_box.delete("1.0", tk.END)
        for widget in chart_frame.winfo_children():
            widget.destroy()

        # Show reviews
        for _, row in df.iterrows():
            review_box.insert(tk.END, f"- {row['review']}\n\n")

        # Show verdict
        verdict = df["verdict"].iloc[0]
        verdict_label.config(
            text=f"Final Verdict: {verdict}", fg="green" if "Positive" in verdict else "red"
        )

        # Show pros & cons
        all_pros = set(sum(df["pros"], []))
        all_cons = set(sum(df["cons"], []))
        pros_label.config(text=f"Pros: {', '.join(all_pros) if all_pros else 'None'}")
        cons_label.config(text=f"Cons: {', '.join(all_cons) if all_cons else 'None'}")

        # Show sentiment chart
        sentiment_counts = df["sentiment"].value_counts()
        fig, ax = plt.subplots(figsize=(4, 3))
        ax.pie(sentiment_counts, labels=sentiment_counts.index, autopct='%1.1f%%', startangle=90)
        ax.set_title("Sentiment Breakdown")

        chart = FigureCanvasTkAgg(fig, master=chart_frame)
        chart.get_tk_widget().pack()
        chart.draw()

        status_label.config(text="✅ Analysis complete")

    def clear_screen():
        entry.delete(0, tk.END)
        review_box.delete("1.0", tk.END)
        verdict_label.config(text="")
        pros_label.config(text="Pros: ")
        cons_label.config(text="Cons: ")
        status_label.config(text="")
        product_label.config(text="")
        buy_button.config(state="disabled")
        for widget in image_frame.winfo_children():
            widget.destroy()
        for widget in chart_frame.winfo_children():
            widget.destroy()

    def go_back_home():
        root.destroy()
        from src.ui.home_ui import open_home_ui  # ✅ import here (lazy, no circular import)
        open_home_ui()

    # ---------------- Buttons ----------------
    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Analyze", command=analyze_product, width=12).grid(row=0, column=0, padx=10)
    tk.Button(btn_frame, text="Clear", command=clear_screen, width=12).grid(row=0, column=1, padx=10)
    tk.Button(btn_frame, text="⬅️ Back to Home", width=15, command=go_back_home).grid(row=0, column=2, padx=10)

    root.mainloop()
