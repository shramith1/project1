import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk, font
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# --- INITIALIZATION & NLTK DATA ---
try:
    sia = SentimentIntensityAnalyzer()
except Exception:
    nltk.download('vader_lexicon')
    sia = SentimentIntensityAnalyzer()

# --- DATABASE LOGIC ---
def init_db():
    conn = sqlite3.connect('hotel_reviews.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            food_item TEXT,
            rating TEXT,
            review_text TEXT,
            sentiment TEXT
        )
    ''')
    conn.commit()
    conn.close()

# --- THEME CONFIGURATION ---
BG_COLOR = "#0F172A"       
CARD_COLOR = "#1E293B"     
ACCENT_COLOR = "#38BDF8"   
GOLD_COLOR = "#FBBF24"     
TEXT_COLOR = "#F8FAFC"
DANGER_COLOR = "#EF4444"

# --- MAIN APP LOGIC ---

def submit_review():
    food = food_var.get()
    rating = rating_combo.get()
    review = review_text.get("1.0", tk.END).strip()

    if food == "--- Select Food Item ---" or not review:
        messagebox.showwarning("Incomplete", "Please select a food item and write a review.")
        return

    score = sia.polarity_scores(review)
    compound = score['compound']
    sentiment = "Positive" if compound >= 0.05 else "Negative" if compound <= -0.05 else "Neutral"

    try:
        conn = sqlite3.connect('hotel_reviews.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO reviews (food_item, rating, review_text, sentiment) VALUES (?, ?, ?, ?)', 
                       (food, rating, review, sentiment))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", f"Feedback Recorded: {sentiment}")
        reset_ui()
    except Exception as e:
        messagebox.showerror("DB Error", f"Error: {e}")

def verify_ownership():
    if owner_entry.get() == "admin" and pass_entry.get() == "hotel123":
        open_dashboard()
    else:
        messagebox.showerror("Auth Error", "Invalid Owner ID or Password")

def logout_owner():
    """Clears login fields when dashboard is closed"""
    owner_entry.delete(0, tk.END)
    pass_entry.delete(0, tk.END)
    root.focus_set() # Moves focus away from the input fields

def open_dashboard():
    dashboard = tk.Toplevel(root)
    dashboard.title("Owner Analytics Panel")
    dashboard.geometry("800x600")
    dashboard.configure(bg=BG_COLOR)
    
    # --- IMPORTANT: Auto-Logout Trigger ---
    # This detects when the owner closes the window
    dashboard.protocol("WM_DELETE_WINDOW", lambda: [logout_owner(), dashboard.destroy()])

    tk.Label(dashboard, text="RESTAURANT ANALYTICS", font=("Helvetica", 18, "bold"), bg=BG_COLOR, fg=ACCENT_COLOR).pack(pady=15)

    # Summary Stats
    conn = sqlite3.connect('hotel_reviews.db')
    cursor = conn.cursor()
    cursor.execute("SELECT sentiment FROM reviews")
    all_s = [r[0] for r in cursor.fetchall()]
    conn.close()

    summary_frame = tk.Frame(dashboard, bg=CARD_COLOR, pady=10)
    summary_frame.pack(fill=tk.X, padx=20, pady=10)
    tk.Label(summary_frame, text=f"Total: {len(all_s)} | Pos: {all_s.count('Positive')} | Neg: {all_s.count('Negative')}", 
             font=("Helvetica", 11), bg=CARD_COLOR, fg=GOLD_COLOR).pack()

    # Table
    tree = ttk.Treeview(dashboard, columns=("Food", "Rating", "Sentiment", "Review"), show='headings')
    tree.heading("Food", text="ITEM")
    tree.heading("Rating", text="RATING")
    tree.heading("Sentiment", text="SENTIMENT")
    tree.heading("Review", text="REVIEW TEXT")
    tree.pack(fill=tk.BOTH, expand=True, padx=20)

    conn = sqlite3.connect('hotel_reviews.db')
    cursor = conn.cursor()
    cursor.execute('SELECT food_item, rating, sentiment, review_text FROM reviews')
    for row in cursor.fetchall():
        tree.insert("", tk.END, values=row)
    conn.close()

    def purge():
        if messagebox.askyesno("Confirm", "Clear all data?"):
            conn = sqlite3.connect('hotel_reviews.db')
            conn.execute('DELETE FROM reviews')
            conn.commit()
            conn.close()
            dashboard.destroy()
            open_dashboard()

    tk.Button(dashboard, text="PURGE DATA", command=purge, bg=DANGER_COLOR, fg="white", font=("Helvetica", 9, "bold"), bd=0, padx=15, pady=8).pack(pady=15)

def reset_ui():
    food_var.set(food_items[0])
    rating_combo.current(0)
    review_text.delete("1.0", tk.END)

# --- USER INTERFACE ---
root = tk.Tk()
root.title("Nexus AI")
root.geometry("500x750")
root.configure(bg=BG_COLOR)

tk.Label(root, text="NEXUS DINING", font=("Helvetica", 24, "bold"), bg=BG_COLOR, fg=ACCENT_COLOR).pack(pady=(40, 5))
tk.Label(root, text="AI SENTIMENT ENGINE", font=("Helvetica", 9), bg=BG_COLOR, fg="#64748B").pack(pady=(0, 30))

form_card = tk.Frame(root, bg=CARD_COLOR, padx=30, pady=30)
form_card.pack(padx=40, fill=tk.X)

# Food List
food_items = ["--- Select Food Item ---", "Paneer Butter Masala", "Chicken Biryani", "Pasta Alfredo", "Margherita Pizza", "Grilled Salmon", "Masala Dosa", "Hakka Noodles"]
food_var = tk.StringVar(value=food_items[0])
ttk.OptionMenu(form_card, food_var, *food_items).pack(fill=tk.X, pady=(5, 20))

# Rating
rating_combo = ttk.Combobox(form_card, values=["⭐⭐⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐", "⭐⭐", "⭐"], state="readonly")
rating_combo.current(0)
rating_combo.pack(fill=tk.X, pady=(5, 20))

# Review
review_text = tk.Text(form_card, height=4, bg=BG_COLOR, fg=TEXT_COLOR, bd=0, font=("Helvetica", 11), padx=10, pady=10, insertbackground="white")
review_text.pack(fill=tk.X, pady=(5, 10))

# Submit
tk.Button(root, text="SUBMIT ANALYSIS", command=submit_review, bg=ACCENT_COLOR, fg=BG_COLOR, font=("Helvetica", 12, "bold"), bd=0).pack(pady=25, padx=40, fill=tk.X, ipady=12)

# --- OWNER LOGIN (CLEARS ON CLOSE) ---
tk.Label(root, text="STAFF LOGIN", font=("Helvetica", 8, "bold"), bg=BG_COLOR, fg="#444").pack(pady=(10, 5))
staff_box = tk.Frame(root, bg=BG_COLOR)
staff_box.pack()

owner_entry = tk.Entry(staff_box, width=15, bg=CARD_COLOR, fg="white", bd=0, font=("Helvetica", 10), justify="center")
owner_entry.grid(row=0, column=0, padx=5, ipady=8)

pass_entry = tk.Entry(staff_box, width=15, bg=CARD_COLOR, fg="white", bd=0, show="*", font=("Helvetica", 10), justify="center")
pass_entry.grid(row=0, column=1, padx=5, ipady=8)

tk.Button(root, text="ACCESS DASHBOARD", command=verify_ownership, bg=BG_COLOR, fg=GOLD_COLOR, font=("Helvetica", 9, "bold"), bd=1, relief="flat").pack(pady=20)

if __name__ == "__main__":
    init_db()
    root.mainloop()