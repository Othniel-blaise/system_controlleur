import cv2

# Capture vidéo à partir de la webcam (index 0)
cap = cv2.VideoCapture(0)

# Définir le codec et créer un objet VideoWriter
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('output.avi', fourcc, 20.0, (640, 480))

while cap.isOpened():
    ret, frame = cap.read()
    if ret:
        # Enregistrer la vidéo
        out.write(frame)

        # Afficher le flux vidéo
        cv2.imshow('Video', frame)

        # Appuyer sur 'q' pour quitter
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    else:
        break

# Libérer les ressources
cap.release()
out.release()
cv2.destroyAllWindows()
