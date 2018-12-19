# Why?

Does a graph database simplify hierarchical classifications?

Suppose we want to build reusable complex classifications. SSN data may occur in 8 places in SFDC. SSN may be a part of PII, HIPAA, and a general PersonalInformation classification that is a part of other, higher level classifications. 

If we add a new connected app which contains SSN, we would like to modify the SSN classification and have all related classifications inherit the changes. Is a graph db easier than existing methods to manage that? To represent that?


