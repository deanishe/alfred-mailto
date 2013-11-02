title: Alfred-MailTo Help
author: deanishe@deanishe.net
date: 2013-10-29


Alfred-MailTo Help
==================

![](screenshot-2.png)

**MailTo** is an Alfred 2 Workflow that allows you to send an email to multiple recipients from your Mac Contacts (or your fingers) with the email client of your choice (or just the boring default one).

## Contents ##

- [TL;DR](#tldr)
- [Usage](#usage)
	- [Prioritising email addresses](#prioritisingemailaddresses)
	- [Groups/Distribution Lists](#groupsdistributionlists)
	- [Selecting and email client](#selectinganemailclient)
	- [Name/address formatting](#nameaddressformatting)
- [Supported clients](#supportedclients)
- [Copyright, licensing etc.](#copyrightlicensingetc)
- [Feedback](#feedback)
- [Technical caveat](#technicalcaveat)

## Usage ##

To start a new mail without recipients, hit `ENTER` on the `Write new email` result.

To add recipients, type `mailto ` (there's a space at the end there!) and start typing the name or email address of someone in your Contacts or the name of a Group/Distribution List (they're the same thing). You can also enter email addresses that aren't in your Contacts database.

Selecting a result and hitting `TAB` will add that email address to the list of recipients, hitting `ENTER` on a result will add that email address to the list of recipients and open the compose window in your selected email client (i.e. closing Alfred's window).

To add further recipients, just keep typing after you've selected the previous one (the email addresses must be separated by a comma).

### Prioritising email addresses ###

**MailTo** uses Alfred's intelligent search to prioritise results you've already selected for the same query. However, this breaks down once there's already one email address in the list.

If the address you want for a contact is always lower down in the results, try moving that address to the top of that persons's list of addresses in Contacts, as a contact's email addresses are shown in the order they appear in Contacts (though the primary email address is always shown first).

This has the additional benefit of having the same effect in Mail.app (unfortunately, other clients are not so smart).

### Groups/Distribution Lists ###

By default, **MailTo** will use the primary or first-listed email address on a contact's card when sending an email to a Group. If you'd prefer to use another email address, open Contacts and use `Edit > Edit Distribution List…` to assign an email address to use when mailing a specific Group.

### Selecting an email client ###

By default, the Workflow uses your system email client, but you can set any client you want using `mailto setdefault APPNAME` (where `APPNAME` is the name of the application, obviously). Just start typing and **MailTo** will show you a list of your apps.

**Note:** you're perfectly free to set an app that doesn't send emails, or does, but doesn't support the `mailto:` protocol. If you do that, you can use choose another app or use `mailto cleardefault` to go back to your system default.

`mailto getdefault` will show you which app you currently have set.

### Name/address formatting ###

By default, **MailTo** sends recipients to your email client with the format `Bob Smith <bob.smith@example.com>`. Some clients can't handle this format, and they will just receive the email address.

Currently, Airmail is the only "blacklisted" client, but if your preferred client also doesn't like the name + email format, you can use `mailto usename` to change the default settings.

## Supported clients ##

In *theory*, any email client should work, as **MailTo** uses the `mailto:` protocol to call your email client. If an email client doesn't support this protocol, give the developers and earful because it really should ;)

The following email clients definitely work:

* Mail.app
* Sparrow
* MailMate
* Unibox
* Thunderbird
* Google Chrome (if you've [set a handler](https://support.google.com/chrome/answer/1382847?hl=en))

The following work with caveats:

* Airmail (only accepts email addresses, no names)

The following do **not** work:

* Safari (it will open your system default mail client instead)

## Copyright, licensing etc. ##

* All the code I wrote is released under the [MIT licence](http://opensource.org/licenses/MIT).
* [alfred.py](https://github.com/nikipore/alfred-python)'s author has indicated no licensing terms that I'm smart enough to find.
* [docopt](http://docopt.org/) is released under the [MIT licence](http://opensource.org/licenses/MIT).
* Email icon from [Icon Archive](http://www.iconarchive.com/show/plex-icons-by-cornmanthe3rd/Communication-email-2-icon.html) is free for personal use.
* Original info icon from [IconsDB](http://www.iconsdb.com/royal-blue-icons/info-icon.html) is CC0 1.0 public domain.
* Original warning icon also from [IconsDB](http://www.iconsdb.com/orange-icons/warning-icon.html) as above.

## Feedback ##

Mail me at <deanishe@deanishe.net>.

## Technical caveat ##

**MailTo** uses a questionable hack: with the official AppleScript access to your Contacts being hopelessly broken, it tries to find and directly access the Contacts/iCloud database files for puma-like speed.

As a result, **MailTo** might break at any time, though the database format has remained stable over several majors version of OS X, and **MailTo** is verified as working on Mountain Lion and Mavericks.

## TL;DR ##

|        Command        |                    Function                    |
| --------------------- | ---------------------------------------------- |
| `mailto `             | Search names, emails, groups                   |
| `mailto getdefault`   | Display currently selected email client        |
| `mailto setdefault`   | Choose email client to use                     |
| `mailto cleardefault` | Use system default email client                |
| `mailto usename`      | Set name/address format to send to your client |
| `mailto help`         | Open this file                                 |
