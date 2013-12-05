title: Alfred-MailTo Help
author: deanishe@deanishe.net
date: 2013-10-29


Alfred-MailTo Help
==================

![](screenshot-2.png)

**MailTo** is an Alfred 2 Workflow that allows you to send an email to multiple recipients from your Mac Contacts (or your fingers) with the email client of your choice (or just the boring default one).

**Note:** Some clients have problems with the default recipient format (name & email address). **MailTo** knows about a few of these clients and how to handle them, but first you have to tell it which email client you're using. See [Selecting an email client](#selectinganemailclient) and [Name/address formatting](#nameaddressformatting) for details.

## Contents ##

- [TL;DR](#tldr)
- [Usage](#usage)
	- [Prioritising email addresses](#prioritisingemailaddresses)
	- [Groups/Distribution Lists](#groupsdistributionlists)
	- [Configuration](#configuration)
		- [Selecting an email client](#selectinganemailclient)
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

### Configuration ###

By default, **MailTo** uses your system default email client and the email format `Bob Smith <bob.smith@example.com>` with clients that support it.

You can view and change your settings with `mailtoconf`.

#### Selecting an email client ####

Change **MailTo**'s email client using `mailtoconf` and select `Change Client …` or directly with `mailtoclient`. Just start typing the name of your preferred client and select it from the list.

**Note:** you're perfectly free to set an app that doesn't send emails, or does, but doesn't support the `mailto:` protocol. If you do that, you choose another app as above.

#### Name/address formatting ####

By default, **MailTo** sends recipients to your email client with the format `Bob Smith <bob.smith@example.com>`. Some email clients, however, require the `mailto:` URL to be constructed in a certain way. **MailTo** knows how to handle many popular email apps, but in some cases you'll have to tell **MailTo** which email client you're using as described in the previous section. See just below for client-specific info.

If you're using an unlisted client and having problems (commas or diacritics in names can cause problems), you can force **MailTo** to call the client with just email addresses (no names). Use `mailtoconf` or `mailtoformat` to do this. If you're having problems with a specific client, [let me know](#feedback) and I'll see what I can do about adding explicit support for it.

## Supported clients ##

In *theory*, any email client should work, as **MailTo** uses the `mailto:` protocol to call your email client. If an email client doesn't support this protocol, give the developers and earful because it really should ;)

If the client does support the protocol, but doesn't work properly with **MailTo**, [let me know](#feedback) and I can possibly add formatting rules for that client.

The following email clients currently work "out of the box":

* Mail.app
* Sparrow
* Thunderbird

The following email clients work, but you have to tell **MailTo** you're using the client:

* Airmail
* Unibox
* MailMate
* Google Chrome (if you've [set a handler](https://support.google.com/chrome/answer/1382847?hl=en))

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

**MailTo** uses a questionable hack: as the official AppleScript access to your Contacts being hopelessly broken, and the Cocoa API is extremely slow when called from Python, it tries to find and directly access the Contacts/iCloud database files for puma-like speed.

As a result, **MailTo** might break at any time, though the database format has remained stable over several majors version of OS X, and **MailTo** is verified as working on Mountain Lion and Mavericks.

## TL;DR ##

|    Command     |                    Function                    |
| -------------- | ---------------------------------------------- |
| `mailto `      | Search names, emails, groups                   |
| `mailtoconf`   | Display and change settings                    |
| `mailtoclient` | Choose email client to use                     |
| `mailtoformat` | Set name/address format to send to your client |
| `mailtohelp`   | See brief help or open this file               |
