#!/usr/bin/python
#
# This converts the feed format used for Swift Playgrounds v1.6 into the subscription format
# used by 2.0. Once converted, you will need to edit the top-level "feed.json" file to fill
# out the following keys:
#
#   title
#   publisherName
#   contactURL
#
# Please refer to the documentation on what these fields should contain.
#
# Also note there is a new field:
#
#   previewImageURLs
#
# that allows preview images to be displayed in the app. Please refer to the documentation for 
# more details.
#
import os
import sys
import json
import argparse
import pprint
import pdb
from shutil import copytree, copy
from copy import deepcopy

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate from old feed format to subscription format.")
    parser.add_argument("-p", "--path", dest="feedPath", required=True, help="Path to the base of the feed to convert (the folder containing the file 'locales.json')")
    parser.add_argument("-o", "--output", dest="outputPath", required=True, help="Path to write the converted feed into")

    pArgs = parser.parse_args()
    
    if not pArgs.feedPath or not pArgs.outputPath:
        print "-p/--path and -o/--output are both required"
        exit(1)
    
    feedPath = os.path.expanduser(pArgs.feedPath)
    outputPath = os.path.expanduser(pArgs.outputPath)

    for folder in [outputPath, os.path.join(outputPath, "Feeds"), os.path.join(outputPath, "Content")]:
        try:
            os.makedirs(folder)
        except OSError as e:
            if e.errno != 17: # File exists. We don't care.
                print("Failed creating folder {}: {}".format(folder, str(e)))
                sys.exit(5)

    baseFeedInfo = { 'formatVersion' : "1.0",
                     'title' : "[Replace Me]",
                     'publisherName' : "[Replace Me]",
                     'feedIdentifier' : "",
                     'contactURL' : "mailto:replaceme@with-something-else.com",
                     'documents' : []
                     }

    locales = {}

    # Find the partner name
    partnerName = next(dir for dir in os.listdir(os.path.join(feedPath, "Partners/Content")) if not dir.startswith("."))
    feedBase = os.path.join(feedPath, "Partners/Content", partnerName, "Feed")
    contentBase = os.path.join(feedPath, "Partners/Content", partnerName, "Content")
    
    contentIdentifiers = []
    
    localizations = filter((lambda x: not x.startswith(".")), os.listdir(feedBase))
    for loc in localizations:
        print "Processing locale '{}'".format(loc)
        locales[loc] = os.path.join("Feeds", loc, "feed.json")
        
        newLocFeed = {"documents" : []}
        contentName = ""
        zipFileName = ""
        
        origLocFeed = os.path.join(feedBase, loc, "feed.json")
        with open(origLocFeed, 'r') as srcFileStream:
            srcJSON = json.load(srcFileStream)
            
            for doc in srcJSON["documents"]:
                newDoc = {}
                newDoc["title"] = doc["title"]
                newDoc["contentIdentifier"] = doc["contentIdentifier"]
                newDoc["sha512"] = doc["SHA512"]
                newDoc["publishedDate"] = doc["metadata"]["publishedDate"]
                newDoc["lastUpdatedDate"] = doc["metadata"]["publishedDate"]
                newDoc["contentVersion"] = "1.0"

                contentIdentifiers.append(newDoc["contentIdentifier"])

                newDoc["url"] = doc["URL"]
                (junk, zipFileName) = os.path.split(newDoc["url"])
                newDoc["thumbnailURL"] = doc["thumbnailURL"]
                (rootImageURLPath, junk) = os.path.split(newDoc["thumbnailURL"])

                detailsPathStub = doc["detailsURL"].replace("../../Content/", "")
                contentName = detailsPathStub.split("/")[0]
                detailsPath = os.path.join(contentBase, detailsPathStub)
                with open(detailsPath, 'r') as detailsFileStream:
                    detailsJSON = json.load(detailsFileStream)
                    
                    # Get from details.json
                    newDoc["description"] = detailsJSON["description"]
                    newDoc["subtitle"] = detailsJSON["subtitle"]
                    newDoc["bannerImageURL"] = os.path.join(rootImageURLPath, detailsJSON["headerImageURL"])
                    newDoc["additionalInformation"] = detailsJSON["additionalInformation"]
                
                # Does not currently exist
                newDoc["previewImageURLs"] = []
                
                newLocFeed["documents"].append(newDoc)
                
                # Copy the details folder over for this locale and content
                folderToCopy = os.path.join(contentBase, contentName, loc)
                destinationPath = os.path.join(outputPath, "Content", contentName, loc)
                copytree(folderToCopy, destinationPath)
        
                # Delete the old details.json file
                os.remove(os.path.join(destinationPath, "details.json"))

                # Then the .zip
                zipFilePath = os.path.join(contentBase, contentName, zipFileName)
                copy(zipFilePath, os.path.join(outputPath, "Content", contentName, zipFileName))

        # Write out the new feed
        newFeed = deepcopy(baseFeedInfo)
        
        # Only take the first two common elements of the identifiers
        newFeed["feedIdentifier"] = str.join(".", os.path.commonprefix(contentIdentifiers).split(".")[slice(2)])
        
        newFeed["documents"] = newLocFeed["documents"]
        os.makedirs(os.path.join(outputPath, "Feeds", loc))
        feedJSON = json.dumps(newFeed, indent=4, sort_keys=False)
        feedFile = open(os.path.join(outputPath, locales[loc]), 'w')
        feedFile.write(feedJSON)
        feedFile.close()

    # Finally, write out locales.json
    correctLocales = {}
    for k,v in locales.iteritems():
        newK = k.replace("_lproj", "")
        correctLocales[newK] = v
        
    localesJSON = json.dumps(correctLocales, indent=4, sort_keys=True)
    localesFile = open(os.path.join(outputPath, "locales.json"), 'w')
    localesFile.write(localesJSON)
    localesFile.close()
    