import os
import subprocess
import shutil
from datetime import datetime

# Définir les variables
work_dir = "/tmp/NXO_Debug"
archive_name = f"Nxo_Debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tgz"
archive_path = f"/tmp/{archive_name}"

# Créer le dossier de travail
os.makedirs(work_dir, exist_ok=True)
log_file = os.path.join(work_dir, "nxo_debug.log")

# Fonction pour écrire les logs
def log(message):
    print(f"[INFO] {message}")
    with open(log_file, "a") as log_f:
        log_f.write(f"[INFO] {message}\n")

# Fonction pour exécuter une commande et gérer les erreurs
def run_command(command, output_file=None):
    try:
        log(f"Exécution : {command}")
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        if output_file:
            with open(os.path.join(work_dir, output_file), "w") as f:
                f.write(result.stdout)
        log("Commande réussie")
    except subprocess.CalledProcessError as e:
        log(f"Erreur lors de l'exécution : {command}")
        log(e.stderr)

# Début du script
log("Début du script de collecte d'informations Checkpoint")

# Étape 1 : Collecte des informations avec cpinfo
run_command("cpinfo -dD -zk")
for file in os.listdir("."):
    if file.endswith(".tgz") or file.endswith(".tar.gz"):
        shutil.move(file, work_dir)

# Étape 2 : Activer les produits et tests HCP
run_command("hcp --enable-product 'Threat Prevention'")
run_command("hcp --enable-product 'Performance'")
run_command("hcp --enable-test 'Protections Impact'")

# Étape 3 : Lancer les diagnostics HCP
run_command("hcp -r all --include-wts yes")

# Étape 4 : Déplacer les fichiers HCP vers le dossier de travail
hcp_last_dir = "/var/log/hcp/last"
if os.path.exists(hcp_last_dir):
    for file in os.listdir(hcp_last_dir):
        shutil.copy(os.path.join(hcp_last_dir, file), work_dir)
else:
    log("Le dossier /var/log/hcp/last n'existe pas")

# Étape 5 : Copier les fichiers messages* vers le dossier de travail
run_command("cp /var/log/messages* /tmp/NXO_Debug/")

# Étape 6 : Copier les fichiers du dossier crash
crash_dir = "/var/log/crash"
if os.path.exists(crash_dir):
    for file in os.listdir(crash_dir):
        shutil.copy(os.path.join(crash_dir, file), work_dir)
else:
    log("Le dossier /var/log/crash n'existe pas")

# Étape 7 : Exécuter les commandes réseau et Checkpoint et stocker les résultats
commands = [
    "ifconfig",
    "cphaprob stat",
    "cphaprob -a if",
    "cphaprob list",
    "cpinfo -y all",
    "enabled_blades",
    "fw stat",
    "ips stat"
]

with open(os.path.join(work_dir, "command_results.txt"), "w") as results_file:
    for command in commands:
        log(f"Exécution de la commande : {command}")
        try:
            result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
            results_file.write(f"### {command} ###\n")
            results_file.write(result.stdout)
            results_file.write("\n")
        except subprocess.CalledProcessError as e:
            log(f"Erreur lors de l'exécution : {command}")
            results_file.write(f"### {command} ###\nErreur lors de l'exécution\n\n")

# Étape 8 : Compression des fichiers
log(f"Compression des fichiers dans {archive_path}")
shutil.make_archive(archive_path.replace(".tgz", ""), 'gztar', work_dir)

# Étape 9 : Suppression des fichiers non compressés dans le dossier de travail
log("Suppression des fichiers non compressés dans le dossier de travail")
for file in os.listdir(work_dir):
    if file != archive_name:
        file_path = os.path.join(work_dir, file)
        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)

# Affichage du chemin du fichier compressé et instructions de fin
log("\nLe script est terminé avec succès.")
log(f"Le fichier compressé se trouve ici : {archive_path}")
log("Vous pouvez désormais envoyer ce fichier au support NXO pour analyse.")
