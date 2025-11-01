# src/ui/history_ui.py
import tkinter as tk
from tkinter import scrolledtext, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import webbrowser

from src.fetch import get_product_info


def open_history_ui(parent):
    parent.destroy()
    root = tk.Tk()
    root.title("📜 History - Analyzed Products")
    root.geometry("900x700")

    tk.Label(root, text="📜 Previously Analyzed Products", font=("Arial", 16, "bold")).pack(pady=10)

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
    frame = tk.Frame(root)
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    review_box = scrolledtext.ScrolledText(frame, wrap=tk.WORD, height=15, width=100)
    review_box.pack(fill="both", expand=True)

    # ---------------- Pros & Cons ----------------
    pros_label = tk.Label(root, text="Pros: ", font=("Arial", 12), fg="green")
    pros_label.pack(pady=5)
    cons_label = tk.Label(root, text="Cons: ", font=("Arial", 12), fg="red")
    cons_label.pack(pady=5)

    # ---------------- Chart Frame ----------------
    chart_frame = tk.Frame(root)
    chart_frame.pack(pady=10)

    # ---------------- Functions ----------------
    def load_history():
        # Clear old
        review_box.delete("1.0", tk.END)
        verdict_label.config(text="")
        pros_label.config(text="Pros: ")
        cons_label.config(text="Cons: ")
        product_label.config(text="")
        buy_button.config(state="disabled")
        for widget in image_frame.winfo_children():
            widget.destroy()
        for widget in chart_frame.winfo_children():
            widget.destroy()

        try:
            df = pd.read_csv("data/analyzed_reviews.csv")
            if df.empty:
                messagebox.showinfo("No Data", "History is empty!")
                return

            # Show latest analysis
            latest = df.iloc[-1]
            product = latest["product"]
            verdict = latest["verdict"]

            # ---- Product info ----
            info = get_product_info(product, max_images=3)

            if info["images"]:
                for i, img in enumerate(info["images"]):
                    tk.Label(image_frame, image=img).grid(row=0, column=i, padx=5)
                    image_frame.image = info["images"]

            product_label.config(text=info["name"])
            if info["buy_url"]:
                buy_button.config(state="normal", command=lambda: webbrowser.open(info["buy_url"]))

            # ---- Reviews ----
            review_box.insert(tk.END, f"📦 Product: {product}\n\n")
            reviews = df[df["product"] == product]["review"].tolist()
            for r in reviews:
                review_box.insert(tk.END, f"- {r}\n\n")

            # ---- Verdict ----
            verdict_label.config(text=f"Final Verdict: {verdict}", fg="green" if "Positive" in verdict else "red")

            # ---- Pros & Cons ----
            pros_label.config(text=f"Pros: {', '.join(eval(latest['pros'])) if latest['pros'] != '[]' else 'None'}")
            cons_label.config(text=f"Cons: {', '.join(eval(latest['cons'])) if latest['cons'] != '[]' else 'None'}")

            # ---- Sentiment chart ----
            sentiment_counts = df["sentiment"].value_counts()
            fig, ax = plt.subplots(figsize=(4, 3))
            ax.pie(sentiment_counts, labels=sentiment_counts.index, autopct='%1.1f%%', startangle=90)
            ax.set_title("Sentiment Breakdown")

            chart = FigureCanvasTkAgg(fig, master=chart_frame)
            chart.get_tk_widget().pack()
            chart.draw()

        except Exception as e:
            messagebox.showerror("Error", f"Could not load history: {e}")

    def clear_screen():
        review_box.delete("1.0", tk.END)
        verdict_label.config(text="")
        pros_label.config(text="Pros: ")
        cons_label.config(text="Cons: ")
        product_label.config(text="")
        buy_button.config(state="disabled")
        for widget in image_frame.winfo_children():
            widget.destroy()
        for widget in chart_frame.winfo_children():
            widget.destroy()

    # ---------------- Buttons ----------------
    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Refresh", command=load_history, width=14).grid(row=0, column=0, padx=10)
    tk.Button(btn_frame, text="Clear", command=clear_screen, width=14).grid(row=0, column=1, padx=10)
    tk.Button(btn_frame, text="Back", command=lambda: [root.destroy(), __import__('home_ui').home_ui.open_home_ui()]).grid(row=0, column=2, padx=10)

    load_history()
    root.mainloop()
