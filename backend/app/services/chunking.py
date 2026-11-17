def decouper(texte: str, taille: int = 200, chevauchement: int = 40) -> list[str]:
    # Each chunk repeats the last `chevauchement` words of the previous one so ideas are not split.
    if chevauchement >= taille:
        raise ValueError("Le chevauchement doit être inférieur à la taille.")

    mots = texte.split()
    pas = taille - chevauchement
    morceaux = []

    for debut in range(0, len(mots), pas):
        morceaux.append(" ".join(mots[debut:debut + taille]))
        if debut + taille >= len(mots):
            break

    return morceaux