# -*- coding: utf-8 -*-
"""
Compresseur d'images moderne avec Glisser-Déposer
Dépendances : Pillow, tkinterdnd2 -> pip install Pillow tkinterdnd2
Lancer     : python main.py
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image

# On essaie d'importer le module de Glisser-Déposer
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")
Image.MAX_IMAGE_PIXELS = 500_000_000


def taille_lisible(nb_octets: int) -> str:
    if nb_octets >= 1024 * 1024:
        return f"{nb_octets / (1024 * 1024):.2f} Mo"
    return f"{nb_octets / 1024:.1f} Ko"


def compresser_image(chemin_src: str, dossier_dest: str, qualite: int,
                     redimensionner: bool, taille_max: int, format_sortie: str) -> tuple:
    nom = os.path.basename(chemin_src)
    nom_sans_ext, ext_origine = os.path.splitext(nom)
    
    with Image.open(chemin_src) as img:
        if format_sortie == "JPEG" and img.mode in ("RGBA", "LA"):
            fond = Image.new("RGB", img.size, (255, 255, 255))
            fond.paste(img, mask=img.split()[-1])
            img = fond
        elif format_sortie == "ORIGINE" and ext_origine.lower() in (".jpg", ".jpeg"):
            img = img.convert("RGB")

        if redimensionner:
            largeur, hauteur = img.size
            if max(largeur, hauteur) > taille_max:
                ratio = taille_max / max(largeur, hauteur)
                img = img.resize((int(largeur * ratio), int(hauteur * ratio)), Image.LANCZOS)

        if format_sortie == "ORIGINE":
            fmt = "WEBP" if ext_origine.lower() == ".webp" else ("PNG" if ext_origine.lower() == ".png" else "JPEG")
            ext_finale = ext_origine.lower()
        else:
            fmt = format_sortie
            ext_finale = ".webp" if format_sortie == "WEBP" else ".jpg"

        nouveau_nom = nom_sans_ext + ext_finale
        chemin_dest = os.path.join(dossier_dest, nouveau_nom)

        if fmt == "PNG":
            img.save(chemin_dest, "PNG", optimize=True)
        elif fmt == "WEBP":
            img.save(chemin_dest, "WEBP", quality=qualite, method=6)
        else:
            img.save(chemin_dest, "JPEG", quality=qualite, optimize=True, progressive=True)

    taille_avant = os.path.getsize(chemin_src)
    taille_apres = os.path.getsize(chemin_dest)
    
    if taille_apres >= taille_avant and ext_origine.lower() == ext_finale:
        os.remove(chemin_dest)
        return (nom, taille_avant, taille_avant)
        
    return (nom, taille_avant, taille_apres)


# On adapte la classe selon la présence de tkinterdnd2
BaseClass = TkinterDnD.Tk if HAS_DND else tk.Tk

class Application(BaseClass):
    def __init__(self):
        super().__init__()
        self.title("Compresseur d'images - Glisser-Déposer")
        self.geometry("700x600")
        self.minsize(600, 500)

        self.fichiers_selectionnes = []
        self._construire_interface()

    def _construire_interface(self):
        tk.Label(self, text="Compresseur d'images Pro", font=("Segoe UI", 18, "bold")).pack(pady=(15, 5))
        
        # Zone de dépôt / Sélection
        self.cadre_depot = tk.LabelFrame(self, text="1. Déposer ou Importer des images", font=("Segoe UI", 10, "bold"))
        self.cadre_depot.pack(pady=10, padx=20, fill="x")

        texte_zone = "Glissez-déposez vos images ICI\nou cliquez pour sélectionner" if HAS_DND else "Cliquez pour sélectionner vos images"
        
        self.bouton_zone = tk.Button(
            self.cadre_depot, text=texte_zone, font=("Segoe UI", 11),
            bg="#eef2fa", fg="#2d6cdf", relief="dashed", bd=2, padding=20,
            command=self.importer_fichiers
        )
        self.bouton_zone.pack(fill="x", padx=10, pady=10)

        if HAS_DND:
            self.bouton_zone.drop_target_register(DND_FILES)
            self.bouton_zone.dnd_bind('<<Drop>>', self.recuperer_fichiers_glisses)

        self.label_statut = tk.Label(self.cadre_depot, text="Aucune image sélectionnée", fg="gray")
        self.label_statut.pack(pady=5)

        # Configuration
        cadre_reglages = tk.LabelFrame(self, text="2. Configuration de sortie", font=("Segoe UI", 10, "bold"))
        cadre_reglages.pack(pady=5, padx=20, fill="x")

        ligne_fmt = tk.Frame(cadre_reglages)
        ligne_fmt.pack(fill="x", padx=10, pady=5)
        tk.Label(ligne_fmt, text="Format cible :", font=("Segoe UI", 10)).pack(side="left")
        self.var_format = tk.StringVar(value="ORIGINE")
        ttk.Radiobutton(ligne_fmt, text="Conserver l'original", variable=self.var_format, value="ORIGINE").pack(side="left", padx=10)
        ttk.Radiobutton(ligne_fmt, text="Forcer WebP", variable=self.var_format, value="WEBP").pack(side="left", padx=10)
        ttk.Radiobutton(ligne_fmt, text="Forcer JPEG", variable=self.var_format, value="JPEG").pack(side="left", padx=10)

        ligne_qualite = tk.Frame(cadre_reglages)
        ligne_qualite.pack(fill="x", padx=10, pady=5)
        tk.Label(ligne_qualite, text="Qualité :", font=("Segoe UI", 10)).pack(side="left")
        self.valeur_qualite = tk.IntVar(value=85)
        tk.Scale(ligne_qualite, from_=40, to=100, orient="horizontal", variable=self.valeur_qualite, length=250).pack(side="left", padx=10)

        self.redimensionner_var = tk.BooleanVar(value=False)
        tk.Checkbutton(cadre_reglages, text="Réduire les dimensions des grandes images", variable=self.redimensionner_var, font=("Segoe UI", 10)).pack(anchor="w", padx=10)
        
        ligne_taille = tk.Frame(cadre_reglages)
        ligne_taille.pack(fill="x", padx=30, pady=2)
        tk.Label(ligne_taille, text="Limite max (pixels) :", font=("Segoe UI", 10)).pack(side="left")
        self.champ_taille = tk.Entry(ligne_taille, width=8)
        self.champ_taille.insert(0, "1920")
        self.champ_taille.pack(side="left", padx=5)

        # Lancer
        self.bouton_lancer = tk.Button(self, text="3. Compresser les images !", command=self.lancer_compression, font=("Segoe UI", 11, "bold"), bg="#28a745", fg="white", padx=20, pady=5, state="disabled")
        self.bouton_lancer.pack(pady=10)

        # Résultats
        cadre_resultats = tk.LabelFrame(self, text="Résultats", font=("Segoe UI", 10, "bold"))
        cadre_resultats.pack(pady=5, padx=20, fill="both", expand=True)

        self.tableau = ttk.Treeview(cadre_resultats, columns=("image", "avant", "après", "gain"), show="headings")
        self.tableau.heading("image", text="Fichier")
        self.tableau.heading("avant", text="Taille Initiale")
        self.tableau.heading("après", text="Taille Compressée")
        self.tableau.heading("gain", text="Réduction")
        self.tableau.column("image", width=250)
        self.tableau.column("avant", width=100, anchor="center")
        self.tableau.column("après", width=100, anchor="center")
        self.tableau.column("gain", width=100, anchor="center")
        
        defilement = tk.Scrollbar(cadre_resultats, orient="vertical", command=self.tableau.yview)
        self.tableau.configure(yscrollcommand=defilement.set)
        self.tableau.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        defilement.pack(side="right", fill="y", pady=5)

    def importer_fichiers(self):
        fichiers = filedialog.askopenfilenames(title="Sélectionner des images", filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.webp")])
        if fichiers:
            self.fichiers_selectionnes = list(fichiers)
            self.label_statut.config(text=f"{len(self.fichiers_selectionnes)} image(s) sélectionnée(s)", fg="black")
            self.bouton_lancer.config(state="normal")

    def recuperer_fichiers_glisses(self, event):
        # Nettoyage du format des chemins envoyés par le Drag & Drop
        data = event.data
        if data.startswith('{'):
            fichiers = [f.strip('{}') for f in data.split('} {')]
        else:
            fichiers = data.split()
        
        valides = [f for f in fichiers if f.lower().endswith(EXTENSIONS)]
        if valides:
            self.fichiers_selectionnes = valides
            self.label_statut.config(text=f"{len(self.fichiers_selectionnes)} image(s) glissée(s) avec succès", fg="black")
            self.bouton_lancer.config(state="normal")

    def lancer_compression(self):
        if not self.fichiers_selectionnes:
            return

        for item in self.tableau.get_children():
            self.tableau.delete(item)

        # On crée un dossier sur le Bureau de l'utilisateur pour le résultat
        bureau = os.path.join(os.path.expanduser("~"), "Desktop")
        dossier_dest = os.path.join(bureau, "Images_Compressees")
        os.makedirs(dossier_dest, exist_ok=True)

        qualite = self.valeur_qualite.get()
        redimensionner = self.redimensionner_var.get()
        format_sortie = self.var_format.get()
        
        try:
            taille_max = int(self.champ_taille.get()) if redimensionner else 0
        except ValueError:
            messagebox.showerror("Erreur", "La taille maximale doit être un nombre valide.")
            return

        succes = 0
        for chemin in self.fichiers_selectionnes:
            try:
                nom, avant, apres = compresser_image(chemin, dossier_dest, qualite, redimensionner, taille_max, format_sortie)
                gain = ((avant - apres) / avant) * 100 if avant > 0 else 0
                self.tableau.insert("", "end", values=(nom, taille_lisible(avant), taille_lisible(apres), f"-{gain:.1f}%"))
                succes += 1
            except Exception as e:
                self.tableau.insert("", "end", values=(os.path.basename(chemin), "Erreur", "-", str(e)))

        messagebox.showinfo("Terminé", f"Traitement fini !\n{succes} image(s) enregistrées sur votre Bureau dans 'Images_Compressees'.")


if __name__ == "__main__":
    app = Application()
    app.mainloop()
