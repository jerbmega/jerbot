# jerbot-neo

jerbot-neo is the **open-source** release of jerbot2, rewritten from scratch so the code is good enough that I feel comfortable open-sourcing it. I wanted to rewrite jerbot2 at some point either way, and figured this would be a good time to do it.

It is missing most functionality of jerbot2 at the moment. Most of jerbot2's features were carry-overs from jerbot1, which was a server-agnostic derivative of 99LBot, which was partially carried over from my old selfbot, which was ported from JS to Python. A fresh rewrite is long overdue. While this will inevitably introduce some new bugs, it will also be much easier to maintain.

## Implemented features
The immediate focus is to lay the groundwork for the rest of the modules. Some simple modules are being tackled, but many will rely on new features in order to be implemented in a cleaner manner, so these are being done first.

* Configuration and cog loading
* Logging, blacklist, auto-message, eagleeye
* (NEW, EXPERIMENTAL) SQLite3 database
* (NEW) Proper moderation command parsing
* (NEW) Announcement system
* (NEW) Global task scheduling

## Planned new features
* The ability  to define multiple API tokens in the main configuration, and easily switch between them using environment vars.
* Proper error handling.
