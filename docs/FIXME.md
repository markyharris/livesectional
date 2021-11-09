# Scrap notes on observations - things to look into more

- Many occurrences of duplication of code
 - Moving to a function and out of webapp.py will improve readability, and make the function available to other code in the environment
- The webpages appear to duplicate a lot of the metar analysis
- There appears to be more external traffic than necessary
 - Can we pull data once - and use it multiple times ?
 - How do we allow end users to configure a proxy for external traffic access


- This device fits into the class of "Internet of Things"
 - It should be secure by default
 - It shouldn't become a hidden launching pad to grant access to the network
 - External connections should be minimized

- Timezone Handling Notes
 - The base OS has a timezone configuration that we shouldn't need to change.
 - There should be an ability to specify the timezone information for any data displayed by the application
 - We shouldn't force the underlying system to align to the application level timezone info
 - 
