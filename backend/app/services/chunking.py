def decouper(texte: str, taille: int = 200, chevauchement: int = 40) -> list[str]:
    """Découpe un texte en morceaux d'environ `taille` mots.

    Chaque morceau reprend les `chevauchement` derniers mots du précédent,
    pour ne pas couper une idée en deux.
    """
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