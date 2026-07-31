"""
Icon catalogue.

Every entry is the exact inner markup of the SVGs used by the original static
design. Storing only a key in the database (validated against these choices)
keeps the rendered markup identical while letting the super admin pick icons.
"""

ICONS = {
    # -- statistics -------------------------------------------------------- #
    "bars": '<path d="M4 18V9M10 18V5M16 18v-6M22 18H2"></path>',
    "check": '<path d="M20 6 9 17l-5-5"></path>',
    "clock": '<circle cx="12" cy="12" r="9"></circle><path d="M12 7v5l3 2"></path>',
    "user": '<path d="M16 20v-2a4 4 0 0 0-8 0v2"></path><circle cx="12" cy="8" r="3.4"></circle>',
    "star": '<path d="m12 4 2.4 5 5.6.8-4 3.9 1 5.5-5-2.7-5 2.7 1-5.5-4-3.9 5.6-.8z"></path>',
    "globe": '<circle cx="12" cy="12" r="8.5"></circle><path d="M3.5 12h17M12 3.5c2.4 2.3 3.6 5.3 3.6 8.5S14.4 18.2 12 20.5c-2.4-2.3-3.6-5.3-3.6-8.5S9.6 5.8 12 3.5z"></path>',
    "rocket": '<path d="M5 15c-1.2 2.2-1 5-1 5s2.8.2 5-1"></path><path d="M14.5 4.5C17 2 21 3 21 3s1 4-1.5 6.5L14 15l-5-5z"></path><circle cx="16" cy="8" r="1.4"></circle>',
    "award": '<circle cx="12" cy="9" r="5.2"></circle><path d="m8.5 13.5-1.3 7L12 18l4.8 2.5-1.3-7"></path>',
    # -- services ---------------------------------------------------------- #
    "code": '<path d="m9 17-5-5 5-5M15 7l5 5-5 5"></path>',
    "browser": '<rect x="3" y="4" width="18" height="14" rx="2.5"></rect><path d="M3 9h18M8 18v2M16 18v2"></path>',
    "redesign": '<path d="M4 14V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v8M2 18h20"></path><path d="m14 8-4 4 4 4"></path>',
    "cart": '<path d="M4 5h2l2.4 10.4A2 2 0 0 0 10.3 17h7.4a2 2 0 0 0 2-1.6L21 8H7"></path><circle cx="10.5" cy="20" r="1.3"></circle><circle cx="18" cy="20" r="1.3"></circle>',
    "search": '<circle cx="11" cy="11" r="6.5"></circle><path d="m20 20-4.4-4.4"></path>',
    "megaphone": '<path d="M4 10v4M4 12c8 0 8-6 16-6v12c-8 0-8-6-16-6"></path>',
    "gear": '<path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1"></path><circle cx="12" cy="12" r="3.2"></circle>',
    "shield": '<path d="M12 3 4 7v6c0 4.4 3.4 7.3 8 8 4.6-.7 8-3.6 8-8V7z"></path><path d="m9 12 2 2 4-4"></path>',
    "phone-device": '<rect x="7" y="3" width="10" height="18" rx="2.4"></rect><path d="M11 18.5h2"></path>',
    "cloud": '<path d="M7 18h10a3.6 3.6 0 0 0 .3-7.2A5.2 5.2 0 0 0 7.2 11 3.5 3.5 0 0 0 7 18z"></path>',
    "database": '<ellipse cx="12" cy="6" rx="7.5" ry="3"></ellipse><path d="M4.5 6v12c0 1.7 3.4 3 7.5 3s7.5-1.3 7.5-3V6"></path><path d="M4.5 12c0 1.7 3.4 3 7.5 3s7.5-1.3 7.5-3"></path>',
    "pen": '<path d="M4 20h4L19.5 8.5a2.1 2.1 0 0 0-3-3L5 17z"></path><path d="M14.5 6.5 17.5 9.5"></path>',
    "chart": '<path d="M4 19V5"></path><path d="M4 19h16"></path><path d="m7.5 15 3.5-4 3 2.5 4.5-6"></path>',
    "lock": '<rect x="4.5" y="10.5" width="15" height="10" rx="2.4"></rect><path d="M8 10.5V8a4 4 0 1 1 8 0v2.5"></path>',
    # -- contact ----------------------------------------------------------- #
    "pin": '<path d="M12 21s7-5.3 7-11a7 7 0 1 0-14 0c0 5.7 7 11 7 11z"></path><circle cx="12" cy="10" r="2.6"></circle>',
    "phone": '<path d="M4 5.5C4 4.7 4.7 4 5.5 4h2c.7 0 1.3.5 1.5 1.2l.7 3a1.5 1.5 0 0 1-.6 1.6l-1.3.9a12 12 0 0 0 5.5 5.5l.9-1.3a1.5 1.5 0 0 1 1.6-.6l3 .7c.7.2 1.2.8 1.2 1.5v2c0 .8-.7 1.5-1.5 1.5A15.5 15.5 0 0 1 4 5.5z"></path>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2.4"></rect><path d="m3.5 7 8.5 6 8.5-6"></path>',
    "hours": '<circle cx="12" cy="12" r="8.5"></circle><path d="M12 7.5V12l3 2"></path>',
    "chat": '<path d="M20 15.5A2.5 2.5 0 0 1 17.5 18H8l-4 3V6.5A2.5 2.5 0 0 1 6.5 4h11A2.5 2.5 0 0 1 20 6.5z"></path>',
    # -- social ------------------------------------------------------------ #
    "linkedin": '<rect x="4" y="4" width="16" height="16" rx="3"></rect><path d="M8 10v6M8 7.5v.01M12 16v-3.2a1.8 1.8 0 0 1 3.6 0V16"></path>',
    "x": '<path d="M5 5l14 14M19 5 5 19"></path>',
    "github": '<path d="M9 19c-4 1.2-4-2.2-5.5-2.8M15 21v-3.4c0-1 .1-1.4-.5-2 2.3-.3 4.5-1.2 4.5-5a3.9 3.9 0 0 0-1-2.7 3.6 3.6 0 0 0-.1-2.7s-1.2-.4-3.9 1.4a9.3 9.3 0 0 0-5 0C6.3 4.8 5.1 5.2 5.1 5.2A3.6 3.6 0 0 0 5 7.9a3.9 3.9 0 0 0-1 2.7c0 3.8 2.2 4.7 4.5 5-.6.6-.6 1.2-.5 2V21"></path>',
    "dribbble": '<circle cx="12" cy="12" r="8.5"></circle><path d="M5 8c5 0 9 1.5 12 5M8.5 20c1.5-6 4-8.5 8-9.5M4.5 14c4-.5 8 1 10 4.5"></path>',
    "facebook": '<path d="M14.5 8.5H17V5h-2.5A4 4 0 0 0 10.5 9v2H8v3.5h2.5V21H14v-6.5h2.5L17 11h-3V9.3c0-.5.2-.8.5-.8z"></path>',
    "instagram": '<rect x="4" y="4" width="16" height="16" rx="4.5"></rect><circle cx="12" cy="12" r="3.6"></circle><path d="M16.8 7.2v.01"></path>',
    "youtube": '<rect x="3" y="6" width="18" height="12" rx="3.5"></rect><path d="m10.5 9.5 5 2.5-5 2.5z"></path>',
    "whatsapp": '<path d="M4 20l1.2-3.6A7.6 7.6 0 1 1 8 19.2z"></path><path d="M9 10c.4 2 2 3.6 4 4l1-1.4 2 .8v1.4c-2.8.5-6.2-2.6-6.6-5.6z"></path>',
    "telegram": '<path d="m21 5-2.6 14L12 15l-2 4-1-5.4L4 11z"></path><path d="m9 13.6 9.5-8"></path>',
    # -- misc -------------------------------------------------------------- #
    "quote": '<path d="M9 7H5.5A2.5 2.5 0 0 0 3 9.5v3A2.5 2.5 0 0 0 5.5 15H7l-1 4 4-5V9a2 2 0 0 0-1-2zM20 7h-3.5A2.5 2.5 0 0 0 14 9.5v3A2.5 2.5 0 0 0 16.5 15H18l-1 4 4-5V9a2 2 0 0 0-1-2z"></path>',
    "moon": '<path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5z"></path>',
    "sun": '<circle cx="12" cy="12" r="4.2"></circle><path d="M12 2.6v2.2M12 19.2v2.2M2.6 12h2.2M19.2 12h2.2M5.4 5.4l1.6 1.6M17 17l1.6 1.6M18.6 5.4 17 7M7 17l-1.6 1.6"></path>',
}


def _choices(keys):
    return [(key, key.replace("-", " ").title()) for key in keys]


STAT_ICON_CHOICES = _choices(
    ["bars", "check", "clock", "user", "star", "globe", "rocket", "award", "chart"]
)

SERVICE_ICON_CHOICES = _choices(
    [
        "code",
        "browser",
        "redesign",
        "cart",
        "search",
        "megaphone",
        "gear",
        "shield",
        "phone-device",
        "cloud",
        "database",
        "pen",
        "chart",
        "lock",
        "rocket",
    ]
)

CONTACT_ICON_CHOICES = _choices(["pin", "phone", "mail", "hours", "chat", "globe"])

SOCIAL_ICON_CHOICES = _choices(
    [
        "linkedin",
        "x",
        "github",
        "dribbble",
        "facebook",
        "instagram",
        "youtube",
        "whatsapp",
        "telegram",
        "mail",
    ]
)

ALL_ICON_CHOICES = _choices(sorted(ICONS))
