
Alfred-MailTo
=============

A Workflow for [Alfred][alfred].

Quickly select recipients from your Mac's Contacts database and send them to your email client of choice. Also works with Groups/Distribution Lists.

![][demo]


Download
--------

You can install MailTo either from [GitHub releases][github-releases].

**Note**: Versions 2.2 and later are only compatible with Alfred 3. If you're using Alfred 2, please install [version v2.1.4][v2.1.4].


Usage
-----

**Note:** The first time you run MailTo, you will probably be asked to grant access to your Contacts. Obviously enough, if you refuse access, MailTo won't work.

Use the `@` keyword in Alfred to access MailTo and search your Mac's Address Book.

Recipients will be suggested from matching contacts and groups in the
accounts configured in your `Contacts` app (see the [help][help] file for supported account types).

Hit `⇥` to autocomplete the recipient list from the selected result, or `↩` or `⌘+NUM` to add the address to the recipient list and start composing a mail.

You can add multiple recipients by adding a comma between them.

Use `mailto` to view/change settings.

See the [online help][help] for more information.


Supported email clients
-----------------------

MailTo *should* work with any email client, as it uses the standard `mailto:` URI scheme to call them.

See the online help for a full list of
[supported and unsupported clients][help-supported-clients].


Contribute
----------

To report a bug or submit a feature request, please create
[an issue on GitHub][github-issues] or [submit a pull request][github-pulls].


Thanks, licensing etc.
----------------------

- The MailTo code is released under the [MIT licence][mit-licence].
- MailTo is heavily based on [Alfred-Workflow][alfred-workflow], also
  released under the [MIT licence][mit-licence] and also by [me][deanishe].
- The icons are almost all from [Dave Gandy][dave-gandy]'s
  [Font Awesome][font-awesome] ([SIL Open Font License][sil-licence]) via [Seth Lilly][seth-lilly]'s also awesome [Font Awesome Symbols for Sketch][font-awesome-sketch] ([MIT licence][mit-licence]). Any icons that are not from Font Awesome, you may do with as you please.


Changelog
---------

### v2.1 (2015-07-28) ###

First non-beta release of v2.


### v2.1.1 (2015-07-28) ###

- Fix typos in `client_rules.json.template`
- Make holding `⌘` down on an email client work as advertised
- Pressing `⌘+L` on an email client shows bundle ID as Large Text


### v2.1.2 (2015-07-30) ###

- Fix settings bug


### v2.1.3 (2015-07-31) ###

- Fix output bug


### v2.1.4 (2016-02-10) ###

- Add Airmail 2 support
- Add MS Outlook support
- Filter duplicate contacts


### v2.2 (2017-09-12) ###

- Update AW library for Sierra compatibility
- Alfred 3-only


### v2.2.1 (2017-09-21) ###

- Revert to using `{query}`


### v2.3 (2017-12-01) ###

- Use `rerun` to reload results after cache updates
- Catch exceptions during group handling


[alfred-workflow]: https://github.com/deanishe/alfred-workflow/
[alfred]: http://www.alfredapp.com/
[dave-gandy]: http://twitter.com/davegandy
[deanishe]: http://twitter.com/deanishe
[demo]: https://github.com/deanishe/alfred-mailto/raw/master/docs/demo.gif
[font-awesome-sketch]: https://github.com/sethlilly/Font-Awesome-Symbols-for-Sketch
[font-awesome]: http://fortawesome.github.io/Font-Awesome/
[github-issues]: https://github.com/deanishe/alfred-mailto/issues
[github-pulls]: https://github.com/deanishe/alfred-mailto/pulls
[github-releases]: https://github.com/deanishe/alfred-mailto/releases/latest
[help-supported-clients]: http://www.deanishe.net/alfred-mailto/#supportedemailclients
[help]: http://www.deanishe.net/alfred-mailto/
[mit-licence]: http://opensource.org/licenses/MIT
[packal-page]: http://www.packal.org/workflow/mailto
[packal-updater]: http://www.packal.org/workflow/packal-updater
[seth-lilly]: http://twitter.com/sethlilly
[sil-licence]: http://scripts.sil.org/OFL
[v2.1.4]: https://github.com/deanishe/alfred-mailto/releases/tag/v2.1.4
