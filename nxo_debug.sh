#!/bin/bash

# Variables
WORK_DIR="/tmp/NXO_Debug"
LOG_FILE="$WORK_DIR/nxo_debug.log"
ARCHIVE_NAME="Nxo_Debug_$(date '+%Y%m%d_%H%M%S').tgz"
ARCHIVE_PATH="/tmp/$ARCHIVE_NAME"

# Créer le dossier de travail
log() {
    echo "[INFO] $1"
    echo "[INFO] $1" >> "$LOG_FILE"
}

log "Création du dossier de travail : $WORK_DIR"
mkdir -p "$WORK_DIR"

# Fonction pour exécuter une commande
run_command() {
    CMD="$1"
    log "Exécution : $CMD"
    eval "$CMD" >> "$LOG_FILE" 2>&1
    if [ $? -ne 0 ]; then
        log "Erreur lors de l'exécution : $CMD"
    else
        log "Commande réussie : $CMD"
    fi
}

log "Début du script de collecte d'informations Checkpoint"

# Étape 1 : Collecte des informations avec cpinfo
run_command "cpinfo -dD -zk"
cpinfo_files=$(find . -name "*.tgz" -o -name "*.tar.gz")
if [ -n "$cpinfo_files" ]; then
    for file in $cpinfo_files; do
        run_command "mv $file $WORK_DIR/"
    done
fi

# Étape 2 : Activer les produits et tests HCP
run_command "hcp --enable-product 'Threat Prevention'"
run_command "hcp --enable-product 'Performance'"
run_command "hcp --enable-test 'Protections Impact'"

# Étape 3 : Lancer les diagnostics HCP
run_command "hcp -r all --include-wts yes"

# Étape 4 : Déplacer les fichiers HCP vers le dossier de travail
if [ -d "/var/log/hcp/last" ]; then
    run_command "cp /var/log/hcp/last/* $WORK_DIR/"
else
    log "Le dossier /var/log/hcp/last n'existe pas"
fi

# Étape 5 : Copier les fichiers messages* vers le dossier de travail
run_command "cp /var/log/messages* $WORK_DIR/"

# Étape 6 : Copier les fichiers du dossier crash
if [ -d "/var/log/crash" ]; then
    run_command "cp -r /var/log/crash/* $WORK_DIR/"
else
    log "Le dossier /var/log/crash n'existe pas"
fi

# Étape 7 : Exécuter les commandes réseau et Checkpoint et stocker les résultats
COMMANDS=(
    "ifconfig"
    "cphaprob stat"
    "cphaprob -a if"
    "cphaprob list"
    "cpinfo -y all"
    "enabled_blades"
    "fw stat"
    "ips stat"
)

for cmd in "${COMMANDS[@]}"; do
    log "Exécution de la commande : $cmd"
    echo "### $cmd ###" >> "$WORK_DIR/command_results.txt"
    $cmd >> "$WORK_DIR/command_results.txt" 2>> "$LOG_FILE"
done

# Étape 8 : Compression des fichiers
log "Compression des fichiers dans $ARCHIVE_PATH"
tar czf "$ARCHIVE_PATH" -C "/tmp" "NXO_Debug"

# Vérification de la création de l'archive
if [ -f "$ARCHIVE_PATH" ]; then
    log "Fichier compressé créé avec succès : $ARCHIVE_PATH"
else
    log "Erreur lors de la création du fichier compressé"
    exit 1
fi

# Étape 9 : Suppression des fichiers non compressés dans le dossier de travail
log "Suppression des fichiers non compressés dans $WORK_DIR"
find "$WORK_DIR" -mindepth 1 ! -name "$ARCHIVE_NAME" -exec rm -rf {} +

# Affichage du chemin du fichier compressé et instructions de fin
echo -e "\n[INFO] Le script est terminé avec succès."
echo "[INFO] Le fichier compressé se trouve ici : $ARCHIVE_PATH"
echo "[INFO] Vous pouvez désormais envoyer ce fichier au support NXO pour analyse."
echo "[INFO] Le fichier compressé se trouve ici : $ARCHIVE_PATH" >> "$LOG_FILE"
echo "[INFO] Vous pouvez désormais envoyer ce fichier au support NXO pour analyse." >> "$LOG_FILE"
