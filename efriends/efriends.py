# coding: utf-8     # noqa: E902
#!/usr/bin/python3  # noqa: E265

"""
Launch efriends application.

Module:    efriends.py
Author:    PQ <pq_rfw @ pm.me>
"""

from views import Views


# ======================
# Main
# ======================

if __name__ == "__main__":
    EF = Views()
    EF.win_root.mainloop()
