#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import qrcode
from PIL import Image, ImageTk
import cv2
import os
from datetime import datetime

class ContactManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Kişi Yönetim Sistemi")
        self.root.geometry("800x600")

        # Database connection
        self.create_database()

        # Main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Input fields for personal information
        ttk.Label(self.main_frame, text="Ad:").grid(row=0, column=0, sticky=tk.W)
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(self.main_frame, textvariable=self.name_var)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.main_frame, text="Soyad:").grid(row=1, column=0, sticky=tk.W)
        self.surname_var = tk.StringVar()
        self.surname_entry = ttk.Entry(self.main_frame, textvariable=self.surname_var)
        self.surname_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(self.main_frame, text="Telefon:").grid(row=2, column=0, sticky=tk.W)
        self.phone_var = tk.StringVar()
        self.phone_entry = ttk.Entry(self.main_frame, textvariable=self.phone_var)
        self.phone_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(self.main_frame, text="E-posta:").grid(row=3, column=0, sticky=tk.W)
        self.email_var = tk.StringVar()
        self.email_entry = ttk.Entry(self.main_frame, textvariable=self.email_var)
        self.email_entry.grid(row=3, column=1, padx=5, pady=5)

        # Buttons
        ttk.Button(self.main_frame, text="Kişi Ekle", command=self.add_contact).grid(row=4, column=0, columnspan=2, pady=10)
        ttk.Button(self.main_frame, text="QR Kod Tara", command=self.scan_qr).grid(row=5, column=0, columnspan=2, pady=5)

        # Contact list
        self.tree = ttk.Treeview(self.main_frame, columns=("ID", "Ad", "Soyad", "Telefon", "E-posta"), show="headings")
        self.tree.grid(row=6, column=0, columnspan=2, pady=10)

        self.tree.heading("ID", text="ID")
        self.tree.heading("Ad", text="Ad")
        self.tree.heading("Soyad", text="Soyad")
        self.tree.heading("Telefon", text="Telefon")
        self.tree.heading("E-posta", text="E-posta")

        # Delete button
        ttk.Button(self.main_frame, text="Seçili Kişiyi Sil", command=self.delete_contact).grid(row=7, column=0, columnspan=2, pady=5)

        # Update contact list
        self.update_contact_list()

    def create_database(self):
        conn = sqlite3.connect('contacts.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS contacts
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     name TEXT NOT NULL,
                     surname TEXT NOT NULL,
                     phone TEXT,
                     email TEXT,
                     qr_path TEXT)''')
        conn.commit()
        conn.close()

    def add_contact(self):
        name = self.name_var.get()
        surname = self.surname_var.get()
        phone = self.phone_var.get()
        email = self.email_var.get()

        if not name or not surname:
            messagebox.showerror("Hata", "Ad ve Soyad alanları zorunludur!")
            return

        # Save to database
        conn = sqlite3.connect('contacts.db')
        c = conn.cursor()
        c.execute("INSERT INTO contacts (name, surname, phone, email) VALUES (?, ?, ?, ?)",
                 (name, surname, phone, email))
        contact_id = c.lastrowid
        
        # Generate QR code
        qr_data = f"ID: {contact_id}\nAd: {name}\nSoyad: {surname}\nTelefon: {phone}\nE-posta: {email}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_image = qr.make_image(fill_color="black", back_color="white")

        # Save QR code
        if not os.path.exists('qr_codes'):
            os.makedirs('qr_codes')
        qr_path = f"qr_codes/contact_{contact_id}.png"
        qr_image.save(qr_path)

        # Save QR code path to database
        c.execute("UPDATE contacts SET qr_path = ? WHERE id = ?", (qr_path, contact_id))
        conn.commit()
        conn.close()

        # Clear form
        self.name_var.set("")
        self.surname_var.set("")
        self.phone_var.set("")
        self.email_var.set("")

        # Update list
        self.update_contact_list()
        messagebox.showinfo("Başarılı", "Kişi başarıyla eklendi!")

    def update_contact_list(self):
        # Clear current list
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Retrieve and list contacts from database
        conn = sqlite3.connect('contacts.db')
        c = conn.cursor()
        c.execute("SELECT id, name, surname, phone, email FROM contacts")
        contacts = c.fetchall()
        conn.close()

        for contact in contacts:
            self.tree.insert("", "end", values=contact)

    def delete_contact(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Uyarı", "Lütfen silinecek kişiyi seçin!")
            return

        if messagebox.askyesno("Onay", "Seçili kişiyi silmek istediğinizden emin misiniz?"):
            contact_id = self.tree.item(selected_item)['values'][0]
            
            conn = sqlite3.connect('contacts.db')
            c = conn.cursor()
            
            # Delete QR code file
            c.execute("SELECT qr_path FROM contacts WHERE id = ?", (contact_id,))
            qr_path = c.fetchone()[0]
            if qr_path and os.path.exists(qr_path):
                os.remove(qr_path)

            # Delete the person from the database
            c.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
            conn.commit()
            conn.close()

            self.update_contact_list()
            messagebox.showinfo("Başarılı", "Kişi başarıyla silindi!")

    def scan_qr(self):
        cap = cv2.VideoCapture(0)
        detector = cv2.QRCodeDetector()

        while True:
            _, img = cap.read()
            data, bbox, _ = detector.detectAndDecode(img)
            
            if data:
                cap.release()
                cv2.destroyAllWindows()
                messagebox.showinfo("QR Kod Bilgisi", data)
                break

            cv2.imshow("QR Kod Tarayıcı", img)
            
            if cv2.waitKey(1) == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    root = tk.Tk()
    app = ContactManager(root)
    root.mainloop()
