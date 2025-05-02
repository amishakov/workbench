#!/usr/bin/env python3

import datetime as dt
from decimal import Decimal as D
from urllib.request import urlopen

import bs4


# ----------------------------------------------------------------------------#
# Autor: Stephan John                                                         #
# Version: 1.0                                                                #
# Datum: 02.04.2010                                                           #
# http://www.it-john.de/weblog/2010/apr/01/berechnung-von-feiertagen/         #
# ----------------------------------------------------------------------------#


class EasterDay:
    """
    Berechnung des Ostersonntages nach der Formel von Heiner Lichtenberg für
    den gregorianischen Kalender. Diese Formel stellt eine Erweiterung der
    Gaußschen Osterformel dar
    Infos unter http://de.wikipedia.org/wiki/Gaußsche_Osterformel
    """

    def __init__(self, year):
        self.year = year

    def get_k(self):
        """
        Säkularzahl:
        K(X) = X div 100
        """

        return self.year // 100

    def get_m(self):
        """
        säkulare Mondschaltung:
        M(K) = 15 + (3K + 3) div 4 − (8K + 13) div 25
        """

        k = self.get_k()
        return 15 + (3 * k + 3) // 4 - (8 * k + 13) // 25

    def get_s(self):
        """
        säkulare Sonnenschaltung:
        S(K) = 2 − (3K + 3) div 4
        """

        k = self.get_k()
        return 2 - (3 * k + 3) // 4

    def get_a(self):
        """
        Mondparameter:
        A(X) = X mod 19
        """

        return self.year % 19

    def get_d(self):
        """
        Keim für den ersten Vollmond im Frühling:
        D(A,M) = (19A + M) mod 30
        """

        a = self.get_a()
        m = self.get_m()
        return (19 * a + m) % 30

    def get_r(self):
        """
        kalendarische Korrekturgröße:
        R(D,A) = D div 29 + (D div 28 − D div 29) (A div 11)
        """

        a = self.get_a()
        d = self.get_d()
        return d // 29 + (d // 28 - d // 29) * (a // 11)

    def get_og(self):
        """
        Ostergrenze:
        OG(D,R) = 21 + D − R
        """

        d = self.get_d()
        r = self.get_r()
        return 21 + d - r

    def get_sz(self):
        """
        erster Sonntag im März:
        SZ(X,S) = 7 − (X + X div 4 + S) mod 7
        """

        s = self.get_s()
        return 7 - (self.year + self.year // 4 + s) % 7

    def get_oe(self):
        """
        Entfernung des Ostersonntags von der Ostergrenze
        (Osterentfernung in Tagen):
        OE(OG,SZ) = 7 − (OG − SZ) mod 7
        """

        og = self.get_og()
        sz = self.get_sz()
        return 7 - (og - sz) % 7

    def get_os(self):
        """
        das Datum des Ostersonntags als Märzdatum
        (32. März = 1. April usw.):
        OS = OG + OE
        """

        og = self.get_og()
        oe = self.get_oe()
        return og + oe

    def get_date(self):
        """
        Ausgabe des Ostersonntags als datetime-Objekt
        """

        os = self.get_os()
        if os > 31:
            month = 4
            day = os - 31
        else:
            month = 3
            day = os
        return dt.date(self.year, month, day)


def get_public_holidays(year):
    easter = EasterDay(year).get_date()

    return {
        dt.date(year, 1, 1): ["Neujahr", D("1")],
        dt.date(year, 1, 2): ["Berchtoldstag", D("1")],
        easter - dt.timedelta(days=3): ["Gründonnerstag", D("0.25")],
        easter - dt.timedelta(days=2): ["Karfreitag", D("1")],
        easter: ["Ostersonntag", D("1")],
        easter + dt.timedelta(days=1): ["Ostermontag", D("1")],
        dt.date(year, 5, 1): ["Tag der Arbeit", D("1")],
        easter + dt.timedelta(days=38): ["Mittwoch vor Auffahrt", D("0.25")],
        easter + dt.timedelta(days=39): ["Auffahrt", D("1")],
        easter + dt.timedelta(days=49): ["Pfingstsonntag", D("1")],
        easter + dt.timedelta(days=50): ["Pfingstmontag", D("1")],
        dt.date(year, 8, 1): ["Nationalfeiertag", D("1")],
        dt.date(year, 12, 24): ["Heiligabend", D("0.5")],
        dt.date(year, 12, 25): ["Weihnachtstag", D("1")],
        dt.date(year, 12, 26): ["Stephanstag", D("1")],
        dt.date(year, 12, 31): ["Silvester", D("0.25")],
    }


def get_zurich_holidays():
    sources = {
        "Knabenschiessen": [
            "https://www.feiertagskalender.ch/kalender.php?geo=3055&jahr=2026&klasse=4&ft_id=60&hl=de",
            D("0.5"),
        ],
        "Sechseläuten": [
            "https://www.feiertagskalender.ch/kalender.php?geo=3055&jahr=2026&klasse=4&ft_id=20&hl=de",
            D("0.5"),
        ],
    }

    days = {}

    for name, (url, fraction) in sources.items():
        with urlopen(url) as response:
            html = response.read()
            soup = bs4.BeautifulSoup(html, "lxml")

            cells = soup.select("table.table-striped tr td:first-child")
            for cell in cells:
                try:
                    day = dt.datetime.strptime(cell.text, "%d.%m.%Y").date()
                except ValueError:
                    continue

                days[day] = [name, fraction]

    return days


if __name__ == "__main__":
    year = dt.date.today().year

    days = get_zurich_holidays()
    for i in range(year, year + 3):
        days |= get_public_holidays(i)
    print(
        "\n".join(
            "{}: {}".format(day.strftime("%d.%m.%Y"), name)
            for day, name in sorted(days.items())
        )
    )
    print()
