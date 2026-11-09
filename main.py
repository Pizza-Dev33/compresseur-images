# -*- coding: utf-8 -*-
"""
Compresseur d'images - Libre et gratuit
Compression avec préservation de la qualité.
Dépendance : Pillow  ->  pip install Pillow
Lancer     :  python main.py
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image

# Extensions reconnues
EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")
Image.MAX_IMAGE_PIXELS = 500_000_000  # sécurité pour très grandes images


def taille_lisible(nb_octets: int) -> str:
    """Convertit une taille en octets vers un texte lisible (Ko, Mo)."""
    if nb_octets >= 1024 * 1024:
        return f"{nb_octets / (1024 * 1024):.2f} Mo"
    return f"{nb_octets / 1024:.1f} Ko"


def compresser_image(chemin_src: str, dossier_dest: str, qualite: int,
                     redimensionner: bool, taille_max: int) -> tuple:
    """
    Compresse une image SANS détruire la qualité :
    - qualité JPEG/WebP réglable (85 = bon compromis recommandé)
    - optimisation des octets sans perte
    - redimensionnement optionnel (jamais agrandir, seulement réduire)
    Retourne (nom, taille_avant, taille_apres) ou lève une exception.
    """
    nom = os.path.basename(chemin_src)
    with Image.open(chemin_src) as img:
        img = img.convert("RGB")

        # Redimensionner seulement si l'image est PLUS GRANDE que la limite
        if redimensionner:
            largeur, hauteur = img.size
            if max(largeur, hauteur) > taille_max:
                ratio = taille_max / max(largeur, hauteur)
                # LANCZOS = meilleur algorithme pour garder la netteté
                img = img.resize((int(largeur * ratio), int(hauteur * ratio)),
                                 Image.LANCZOS)

        # On enregistre toujours en JPEG : c'est là que le gain de poids se fait.
        # Si la compression rendait le fichier PLUS LOURD, on garde l'original.
        nouveau_nom = os.path.splitext(nom)[0] + ".jpg"
        chemin_dest = os.path.join(dossier_dest, nouveau_nom)

        img.save(chemin_dest, "JPEG",
                 quality=qualite,       # niveau de qualité choisi
                 optimize=True,         # compression optimale sans perte visuelle
                 progressive=True)      # chargement progressif sur le web

    taille_avant = os.path.getsize(chemin_src)
    taille_apres = os.path.getsize(chemin_dest)
    if taille_apres >= taille_avant:
        os.remove(chemin_dest)
        return (nom, taille_avant, taille_avant)
    return (nom, taille_avant, taille_apres)


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Compresseur d'images - gratuit, sans pub")
        self.geometry("680x520")
        self.minsize(560, 460)

        self.dossier_source = ""
        self.resultats = []

        self._construire_interface()

    def _construire_interface(self):
        # --- Titre ---
        titre = tk.Label(self, text="Compresseur d'images",
                         font=("Segoe UI", 18, "bold"))
        titre.pack(pady=(15, 5))
        sous_titre = tk.Label(self,
                              text="Qualité préservée · 100 % gratuit · fonctionne hors ligne",
                              font=("Segoe UI", 10), fg="gray")
        sous_titre.pack()

        # --- Choix du dossier ---
        cadre_choix = tk.Frame(self)
        cadre_choix.pack(pady=15, padx=20, fill="x")

        self.bouton_choisir = tk.Button(
            cadre_choix, text="1. Choisir un dossier d'images",
            command=self.choisir_dossier, font=("Segoe UI", 11),
            bg="#2d6cdf", fg="white", padx=10, pady=5)
        self.bouton_choisir.pack()

        self.label_dossier = tk.Label(cadre_choix, text="Aucun dossier choisi",
                                      fg="gray", wraplength=600)
        self.label_dossier.pack(pady=5)

        # --- Réglages qualité ---
        cadre_reglages = tk.LabelFrame(self, text="2. Réglages qualité",
                                       font=("Segoe UI", 10))
        cadre_reglages.pack(pady=5, padx=20, fill="x")

        ligne_qualite = tk.Frame(cadre_reglages)
        ligne_qualite.pack(fill="x", padx=10, pady=(8, 2))
        tk.Label(ligne_qualite, text="Qualité :",
                 font=("Segoe UI", 10)).pack(side="left")
        self.valeur_qualite = tk.IntVar(value=85)
        self.curseur = tk.Scale(
            ligne_qualite, from_=40, to=100, orient="horizontal",
            variable=self.valeur_qualite, length=300)
        self.curseur.pack(side="left", padx=10)
        tk.Label(ligne_qualite, text="(85 = recommandé, la qualité reste très bonne)",
                 font=("Segoe UI", 9), fg="gray").pack(side="left")

        # --- Redimensionnement optionnel ---
        self.redimensionner_var = tk.BooleanVar(value=False)
        coche = tk.Checkbutton(
            cadre_reglages, text="Réduire aussi les très grandes images (optionnel)",
            variable=self.redimensionner_var, font=("Segoe UI", 10))
        coche.pack(anchor="w", padx=10)

        ligne_taille = tk.Frame(cadre_reglages)
        ligne_taille.pack(fill="x", padx=10, pady=(2, 8))
        tk.Label(ligne_taille, text="Taille maximale (pixels) :",
                 font=("Segoe UI", 10)).pack(side="left")
        self.champ_taille = tk.Entry(ligne_taille, width=8)
        self.champ_taille.insert(0, "1920")
        self.champ_taille.pack(side="left", padx=5)
        tk.Label(ligne_taille, text="(ex. 1920 = idéal pour le web)",
                 font=("Segoe UI", 9), fg="gray").pack(side="left")

        # --- Bouton lancer ---
        self.bouton_lancer = tk.Button(
            self, text="3. Compresser !", command=self.lancer_compression,
            font=("Segoe UI", 12, "bold"), bg="#28a745", fg="white",
            padx=20, pady=6, state="disabled")
        self.bouton_lancer.pack(pady=10)

        # --- Résultats ---
        cadre_resultats = tk.LabelFrame(self, text="Résultats",
                                        font=("Segoe UI", 10))
        cadre_resultats.pack(pady=5, padx=20, fill="both", expand=True)

        colonnes = ("image", "avant", "après", "gain")
        self.tableau = ttk.Treeview(cadre_resultats, columns=colonnes,
                                     show="headings", height=8)
        self.tableau.heading("image", text="Image")
        self.tableau.heading("avant", text="Avant")
        self.tableau.heading("après", text="Après")
        self.tableau.heading("gain", text="Gain")
        self.tableau.column("image", width=260)
        self.tableau.column("avant", width=90, anchor="center")
        self.tableau.column("après", width=90, anchor="center")
        self.tableau.column("gain", width=80, anchor="center")

        defilement = tk.Scrollbar(cadre_resultats, orient="vertical",
                                  command=self.tableau.yview)
        self.tableau.configure(yscrollcommand=defilement.set)
        self.tableau.pack(side="left", fill="both", expand=True, padx=(5, 0),
                          pady=5)
        defilement.pack(side="right", fill="y", pady=5, padx=(0, 5))

    # ---------- Actions ----------

    def choisir_dossier(self):
        dossier = filedialog.askdirectory(title="Choisir le dossier contenant les images")
        if dossier:
            self.dossier_source = dossier
            nb = len([f for f in os.listdir(dossier)
                      if f.lower().endswith(EXTENSIONS)])
            self.label_dossier.config(
                text=f"{dossier}  ({nb} image(s) trouvée(s))", fg="black")
            self.bouton_lancer.config(state="normal")

    def lancer_compression(self):
        if not self.dossier_source:
            messagebox.showwarning("Attention", "Choisis d'abord un dossier.")
            return

        # Dossier de sortie : "images_compressees" à côté du dossier source
        dossier_dest = os.path.join(self.dossier_source, "images_compressees")
        os.makedirs(dossier_dest, exist_ok=True)

        qualite = self.valeur_qualite.get()
        redimensionner = self.redimensionner_var.get()
        try:
            taille_max = int(self.champ_taille.get()) if redimensionner else 0
        except ValueError:
            messagebox.showerror("Erreur", "La taille maximale doit être un nombre.")
            return

        fichiers = sorted(f for f in os.listdir(self.dossier_source)
                          if f.lower().endswith(EXTENSIONS))
        if not fichiers:
            messagebox.showinfo("Info", "Aucune image trouvée dans ce dossier.")
            return

        # Nettoyer les anciens résultats
        for ligne in self.tableau.get_children():
            self.tableau.delete(ligne)

        self.bouton_lancer.config(text="Compression en cours...", state="disabled")
        self.update_idletasks()

        total_avant = 0
        total_apres = 0
        erreurs = 0

        for nom in fichiers:
            chemin = os.path.join(self.dossier_source, nom)
            try:
                _, avant, apres = compresser_image(
                    chemin, dossier_dest, qualite, redimensionner, taille_max)
                total_avant += avant
                total_apres += apres
                gain = (1 - apres / avant) * 100 if avant else 0
                self.tableau.insert("", "end", values=(
                    nom, taille_lisible(avant), taille_lisible(apres),
                    f"-{gain:.0f} %"))
            except Exception as erreur:
                erreurs += 1
                self.tableau.insert("", "end", values=(
                    nom, "Erreur", str(erreur)[:40], "-"))
            self.update_idletasks()

        if total_avant:
            gain_global = (1 - total_apres / total_avant) * 100
            self.tableau.insert("", "end", values=(
                "TOTAL", taille_lisible(total_avant),
                taille_lisible(total_apres), f"-{gain_global:.0f} %"))

        self.bouton_lancer.config(text="3. Compresser !", state="normal")

        message = (f"Terminé ! {len(fichiers) - erreurs} image(s) compressée(s)"
                   f" dans :\n{dossier_dest}")
        if erreurs:
            message += f"\n\n{erreurs} image(s) en erreur."
        messagebox.showinfo("Compression terminée", message)


if __name__ == "__main__":
    app = Application()
    app.mainloop()
