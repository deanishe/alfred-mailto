//
//  main.m
//  CacheContacts
//
//  Created by Dean Jackson on 17/10/2014.
//  Copyright (c) 2014 Dean Jackson. All rights reserved.
//

#import <Foundation/Foundation.h>
#import <CoreFoundation/CoreFoundation.h>
#import <AddressBook/AddressBook.h>

int main(int argc, const char * argv[]) {
    @autoreleasepool {
        CFAbsoluteTime startTime = CFAbsoluteTimeGetCurrent();
        ABAddressBook *AB = [ABAddressBook sharedAddressBook];

        /*
         {
         'name': "Person's or company name",  # may be empty
         'email': 'email.address@example.com',
         'nickname': "Contact's nickname",
         'company': "Name of contact's company",
         'is_group': True/False,
         'is_company': True/False,
         'key': nickname + name + email,
         }
        */
        NSMutableArray *contacts = [NSMutableArray array];
        /*
         {
         'email.address@example.com': "Person's or company name",
         ...
         }
        */
        NSMutableDictionary *email_name_map = [NSMutableDictionary dictionary];

        NSLog(@"%lu people and %lu groups in Address Book", (unsigned long)[[AB people] count], [[AB groups] count]);
        
        // Name ordering
        NSInteger defaultNameOrdering = AB.defaultNameOrdering;

        // Add people to cache
        for (ABPerson *person in [AB people]) {

            // Initialise contact
            NSMutableDictionary *contact = [NSMutableDictionary dictionary];

            [contact setValue:[NSNumber numberWithBool:NO] forKey:@"is_company"];
            [contact setValue:[NSNumber numberWithBool:NO] forKey:@"is_group"];

            NSString *nickname  = [person valueForProperty:kABNicknameProperty];
            NSString *firstName = [person valueForProperty:kABFirstNameProperty];
            NSString *lastName  = [person valueForProperty:kABLastNameProperty];
            NSString *company   = [person valueForProperty:kABOrganizationProperty];
            NSArray  *emailIds  = [person valueForProperty:kABEmailProperty];

            if ([emailIds count] == 0) {
                // No use to us
                continue;
            }

            NSMutableArray *emails = [NSMutableArray array];
            for (int i=0; i<[emailIds count]; i++) {
                [emails addObject:[emailIds valueAtIndex:i]];
            }

            if (nickname == nil) {
                nickname = @"";
            }
            if (firstName == nil) {
                firstName = @"";
            }
            if (lastName == nil) {
                lastName = @"";
            }
            if (company == nil) {
                company = @"";
            }

            NSString *name = nil;
            
            if (defaultNameOrdering == kABLastNameFirst) {
                name = [[[lastName stringByAppendingString:@", "]
                               stringByAppendingString:firstName]
                              stringByTrimmingCharactersInSet:[NSCharacterSet
                                                               whitespaceAndNewlineCharacterSet]];
            } else {
                name = [[[firstName stringByAppendingString:@" "]
                         stringByAppendingString:lastName]
                        stringByTrimmingCharactersInSet:[NSCharacterSet
                                                         whitespaceAndNewlineCharacterSet]];
            }
            if ([name length] == 0) {
                if (company != nil) {
                    name = company;
                    [contact setValue:[NSNumber numberWithBool:YES] forKey:@"is_company"];
                }
            }

            [contact setObject:name forKey:@"name"];
            [contact setObject:nickname forKey:@"nickname"];
            [contact setObject:company forKey:@"company"];

            for (NSString *email in emails) {
                [email_name_map setValue:name forKey:email];
                NSString *msg = [[[name stringByAppendingString:@" <"]stringByAppendingString:email]stringByAppendingString:@">"];
                if ([nickname length] > 0) {
                    msg = [[[msg stringByAppendingString:@" ("] stringByAppendingString:nickname]stringByAppendingString:@")"];
                }
                NSLog(@"%@", msg);
                NSArray *keyComponents = @[nickname, name, email];
                NSString *key = [keyComponents componentsJoinedByString:@" "];
                [contact setObject:key forKey:@"key"];
                [contact setObject:email forKey:@"email"];
                [contacts addObject:contact];

            }

//            if ([emails count] > 1) {
//                NSLog(@"%lu email addresses for %@", (unsigned long)[emails count], name);
//            }

        }

        // Add groups to cache
        for (ABGroup *group in [AB groups]) {
            NSMutableDictionary *contact = [NSMutableDictionary dictionary];
            [contact setObject:[NSNumber numberWithBool:YES] forKey:@"is_group"];
            [contact setObject:[NSNumber numberWithBool:NO] forKey:@"is_company"];
            [contact setObject:[group valueForProperty:kABGroupNameProperty] forKey:@"name"];

            // Add emails
            NSMutableArray *emails = [NSMutableArray array];
//            NSLog(@"Members of '%@'", [contact objectForKey:@"name"]);
            for (ABPerson *person in [group members]) {
                NSString *identifier = [group distributionIdentifierForProperty:kABEmailProperty person:person];
                if (identifier != nil) {
                    ABMultiValue *personEmails = [person valueForProperty:kABEmailProperty];
                    NSString *email = [personEmails valueAtIndex:[personEmails indexForIdentifier:identifier]];
//                    NSLog(@"\t%@", email);
                    [emails addObject:email];
                }
            }

            if ([emails count] == 0) {  // Ignore empty groups
                continue;
            }

            NSLog(@"%lu people in '%@'", [emails count], [contact objectForKey:@"name"]);

            [contact setObject:[emails componentsJoinedByString:@","] forKey:@"email"];
            [contacts addObject:contact];
//            NSLog(@"%@ : %@", [contact valueForKey:@"name"], [contact valueForKey:@"email"]);

        }

        CFAbsoluteTime endTime = CFAbsoluteTimeGetCurrent();
        double elapsed = endTime - startTime;
        NSLog(@"Cached %lu emails/groups in %0.3f seconds", (unsigned long)[contacts count], elapsed);

        NSDictionary *cacheData = [NSDictionary dictionaryWithObjectsAndKeys:contacts, @"contacts", email_name_map, @"email_name_map", nil];

        // Generate and output JSON
        NSData *encodedData = [NSJSONSerialization dataWithJSONObject:cacheData options:NSJSONWritingPrettyPrinted error:nil];
        NSString *jsonString = [[NSString alloc] initWithData:encodedData encoding:NSUTF8StringEncoding];
        [jsonString writeToFile:@"/dev/stdout" atomically:NO encoding:NSUTF8StringEncoding error:nil];

        NSLog(@"defaultNameOrdering %06o", (unsigned int)defaultNameOrdering);
        
    }
    return 0;
}
