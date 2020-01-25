# Race-Simulation

Use Psi to comunicate with agents: https://psi-im.org/


# scrapping, defining EnvironmentAgentBehaviour instead


# Zachowanie Agenta Środowisko
# 1) REJESTRACJA NA WYŚCIG
# - informuje liste znanych kierowców o wyścigu
# - bierze pierwszych x (np. 6) samochodów i dodaje do wyścigu
# - za malo kierowcow po czasie - poinformuj o tym i zakoncz
# - timeout 5 sekund - wszystkie pozostale pola w wyścigu zostaw puste
# - zapisz aktywnych kierowców w wyścigu i przygotuj filtr na przyjmowanie komunikacji tylko od nich (Template)
# 2) KONIEC REJESTRACJI - INICJALIZACJA KIEROWCÓW - przekaz danych o torze wyścigu itp. start po 5 sek od końca rejestracji
# 3) START - wyślij info o starcie kierowcom wyścigu
# 4) SYMULACJE
# - polling z czestotliwością 30x/sek
# - update do kierowców - ile czasu upłyneło od ostatniego update + stan: (droga, predkosc, przyspieszenie)
# - asynchronicznie zbierać wiadomości od kierowców (przyspieszenie: x) i ustawiać parametry modelu
# 5) FINISH
# - po zadanym czasie przekaż raport dla StarterAgenta żeby odesłał do użytkownika