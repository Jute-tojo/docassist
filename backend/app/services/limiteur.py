import threading
import time
from collections import defaultdict, deque


class Limiteur:
    """In-memory sliding-window rate limiter (one process; resets on restart)."""

    def __init__(self, max_requetes: int, fenetre_secondes: int = 60):
        self.max_requetes = max_requetes
        self.fenetre = fenetre_secondes
        self._appels: dict[str, deque[float]] = defaultdict(deque)
        self._verrou = threading.Lock()

    def autoriser(self, cle: str) -> bool:
        maintenant = time.monotonic()
        with self._verrou:
            appels = self._appels[cle]
            while appels and maintenant - appels[0] > self.fenetre:
                appels.popleft()
            if len(appels) >= self.max_requetes:
                return False
            appels.append(maintenant)
            return True
