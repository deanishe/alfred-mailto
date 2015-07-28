//
//  main.m
//  CacheMailApps
//
//  Created by Dean Jackson on 19/10/2014.
//  Copyright (c) 2014 Dean Jackson. All rights reserved.
//

#import <Foundation/Foundation.h>
#import <CoreServices/CoreServices.h>


NSDictionary* appInfo(NSURL *appURL) {
    NSString *appPath = [appURL path];
    NSString *appName = [[appPath stringByDeletingPathExtension] lastPathComponent];
    NSBundle *appBundle = [NSBundle bundleWithURL:appURL];
    NSString *bundleIdentifier = [appBundle bundleIdentifier];
    NSDictionary *app = [NSDictionary dictionaryWithObjectsAndKeys:appPath, @"path", appName, @"name", bundleIdentifier, @"bundleid", nil];
    NSLog(@"%@", app);
    return app;
}

int main(int argc, const char * argv[]) {
    @autoreleasepool {
        CFAbsoluteTime startTime = CFAbsoluteTimeGetCurrent();
        NSMutableArray *handlers = [NSMutableArray array];
        NSDictionary *defaultHandler = [NSDictionary dictionary];
        // Get all mailto handlers
        CFURLRef urlRef = (__bridge CFURLRef)[NSURL URLWithString:@"mailto:test@example.com"];
        CFArrayRef URLs = LSCopyApplicationURLsForURL(urlRef, kLSRolesAll);

        if (URLs != NULL) {
            CFIndex i, c = CFArrayGetCount(URLs);
            CFURLRef curURL;

            for (i=0l; i<c; i++) {
                curURL = CFArrayGetValueAtIndex(URLs, i);
                NSURL *url = (__bridge NSURL*)curURL;
                NSDictionary *app = appInfo(url);
                [handlers addObject:app];
            }
        }

        // Get default handler
        CFURLRef URL = NULL;
        LSGetApplicationForURL(urlRef, kLSRolesAll, NULL, &URL);

        if (URL != NULL) {
            NSURL *defaultURL = (__bridge NSURL*)URL;
            NSLog(@"Default mailto: handler: %@", defaultURL);
            defaultHandler = appInfo(defaultURL);
        }

        // Generate and output JSON
        NSDictionary *cacheData = [NSDictionary dictionaryWithObjectsAndKeys:defaultHandler, @"system_default_app", handlers, @"all_apps", nil];
        NSData *encodedData = [NSJSONSerialization dataWithJSONObject:cacheData options:NSJSONWritingPrettyPrinted error:nil];
        NSString *jsonString = [[NSString alloc] initWithData:encodedData encoding:NSUTF8StringEncoding];
        [jsonString writeToFile:@"/dev/stdout" atomically:NO encoding:NSUTF8StringEncoding error:nil];

        CFTimeInterval elapsed = CFAbsoluteTimeGetCurrent() - startTime;
        NSLog(@"%lu mailto: handlers found in %0.3f seconds", (unsigned long)[handlers count], elapsed);

    }
    return 0;
}
