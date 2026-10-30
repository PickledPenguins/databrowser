"""A page carrying a data-sharing notice at the bottom."""

from databrowser import GroupPage, Theme

theme = Theme(bottom_banner="Clinical imaging core - imaging@hospital.example\nPseudonymized data, internal use only")
GroupPage("site/index.html", "MRI sessions, study 22", ["Session", "Scans"], footer="Exported 2026-10-29",
          theme=theme).write()
