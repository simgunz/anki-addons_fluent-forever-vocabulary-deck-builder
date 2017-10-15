Fluent forever vocabulary deck builder
======================================

Fluent Forever vocabulary deck builder is an open source add-on for Anki, which aims to speed up the creation of vocabulary decks used to learn a language with the Fluent Forever method. The add-on gathers automatically all the information required to construct a card such as pictures, pronunciation audio, IPA transcription, etc. and propose them to the user, which will take the final decision on which media represent best the current word based on its own personal connections. In this way the user is not bothered in finding the data, and can stay focused only on the learning process, thus saving a lot of time.

This project is in no way associated to fluent-forever.com, but it just aims to be a tool to implement the fluent forever method proposed by Gabriel Wyner.

Project status
==============

The add-on was originally developed for anki 2.0.x.

Due to changes in the distribution of the PyQt libraries, this add-on doesn't work out of the box with the latest version of Anki 2.0.47. Probably it is possible to install all the required dependencies and make it work.

This add-on is not compatible with the upcoming Anki 2.1, which underwent a lot of changes in the core of the code. A porting of the add-on for Anki 2.1 has started but it is still in a state where it is not working.

See the DEVELOP file for more information and [Issue 1](https://github.com/simgunz/anki-addons_fluent-forever-vocabulary-deck-builder/issues/2).

Current features
=====================
- Gallery loading from Bing images (requires API key, ugly looking)
- Automatic image rescaling (to minimize disk space and speed up loading in anki)
- Download audio from Forvo (requires API key)
- Filter noise and normalize volume form audio tracks
- IPA download from Wiktionary [on a separate branch]
- Preloading
- Embed of Wikitionary and a custom website to manually lookup definitions (and other information) [on a separate branch]
- Configuration dialog to setup API keys and select current language
- Anki browser navigation buttons (Previous, Next)

Project management
==================
Initially issues and ideas were managed using this [Trello board] (https://trello.com/b/Q7h3sRoq/anki-vocabulary-deck-builder).
From now on I am planning to slowly move everything to github issues and github project.

Author
======
Simone Gaiarin \<simgunz AT gmail DOT com\>

License
=======
Software distributed under the GNU General Public License version 3 (GNU GPL v3).

http://www.gnu.org/copyleft/gpl.html

References
=============
* [Fluent forever](https://fluent-forever.com/)
* [Github page](https://github.com/simgunz/anki-addons_fluent-forever-vocabulary-deck-builder/)
