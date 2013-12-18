import xml
from xml.dom.minidom import Document
from collections import namedtuple
from xml.etree.ElementTree import Element, SubElement, Comment, tostring
from xml.etree import ElementTree
from xml.dom import minidom
import time
import re

"""
create classes to represent affiliations, authors and papers.
pass the compount object to a calss that writes the XML in the expected format. 

## GOTCHAS/TODOs

self.orcid.set("xlink:href", contributor.orcid) returns an error

in aff, determine why some elements take an enclosing addr-line, and others don't 

in aff, if email is associated with aff, how do we deal with two atuhors from the same place,
but with different emails?

Think about moving the function that adds the doctype out of the funciton that 
does pretty printing. 
"""

class eLife2XML(object):
    root = Element('article')

    def __init__(self, poa_article):
        """
        set the root node
        get the article type from the object passed in to the class
        set default values for items that are boilder plate for this XML 
        """

        # set the boiler plate values
        self.journal_id_types = ["nlm-ta", "hwp", "publisher-id"]
        self.date_types = ["accepted", "received"]
        self.elife_journal_id = "eLife"
        self.elife_journal_title = "eLife"
        self.elife_epub_issn = "2050-084X"
        self.elife_publisher_name = "eLife Sciences Publications, Ltd"

        self.root.set('article-type', poa_article.articleType)
        self.root.set('xmlns:xlink', 'http://www.w3.org/1999/xlink')
        comment = Comment('generated by eLife')
        self.root.append(comment)
        self.build(self.root, poa_article)

    def build(self, root, poa_article):
        self.set_frontmatter(self.root, poa_article)
        # self.set_title(self.root, poa_article)

    def set_frontmatter(self, parent, poa_article):
        self.front = SubElement(parent, 'front')
        self.set_journal_meta(self.front)
        self.set_article_meta(self.front, poa_article)        


    def set_article_meta(self, parent, poa_article):
        self.article_meta = SubElement(parent, "article-meta")
        
        # article-id pub-id-type="manuscript"
        if poa_article.manuscript:
            pub_id_type = "manuscript"
            self.article_id = SubElement(self.article_meta, "article-id") 
            self.article_id.text = str(int(poa_article.manuscript)).zfill(5)
            self.article_id.set("pub-type-id", pub_id_type) 
        
        # article-id pub-id-type="doi"
        if poa_article.doi:
            pub_id_type = "doi"
            self.article_id = SubElement(self.article_meta, "article-id") 
            self.article_id.text = poa_article.doi
            self.article_id.set("pub-type-id", pub_id_type)
        
        # article-categories
        self.set_article_categories(self.article_meta, poa_article)
        #
        self.title_group = SubElement(self.article_meta, "title-group")
        self.title = SubElement(self.title_group, "article-title")
        self.title.text = poa_article.title 
        #
        self.set_contrib_group(self.article_meta, poa_article)
        #
        self.set_pub_date(self.article_meta, poa_article, "epub")
        #
        if poa_article.dates:
            self.set_history(self.article_meta, poa_article)
        #
        if poa_article.license:
            self.set_permissions(self.article_meta, poa_article)
        #
        self.set_abstract = SubElement(self.article_meta, "abstract")
        self.set_para = SubElement(self.set_abstract, "p")
        self.set_para.text = poa_article.abstract

    def set_journal_title_group(self, parent):
        """
        take boiler plate values from the init of the class 
        """
        
        # journal-title-group
        self.journal_title_group = SubElement(parent, "journal-title-group")

        # journal-title
        self.journal_title = SubElement(self.journal_title_group, "journal-title")
        self.journal_title.text = self.elife_journal_title 

    def set_journal_meta(self, parent):
        """
        take boiler plate values from the init of the calss 
        """
        self.journal_meta = SubElement(parent, "journal-meta")

        # journal-id
        for journal_id_type in self.journal_id_types:
            self.journal_id = SubElement(self.journal_meta, "journal-id") 
            self.journal_id.text = self.elife_journal_id 
            self.journal_id.set("journal-id-type", journal_id_type) 

        #
        self.set_journal_title_group(self.journal_meta)

        # title-group
        self.issn = SubElement(self.journal_meta, "issn")
        self.issn.text = self.elife_epub_issn
        self.issn.set("pub-type", "epub")

        # publisher
        self.publisher = SubElement(self.journal_meta, "publisher")
        self.publisher_name = SubElement(self.publisher, "publisher-name")
        self.publisher_name.text = self.elife_publisher_name

    def set_license(self, parent, poa_article):
        self.license = SubElement(parent, "license")
        self.license.set("license-type", poa_article.license.license_type)
        self.license.set("xlink:href", poa_article.license.href)
        
        self.license_p = SubElement(self.license, "license-p")
        self.license_p.text = poa_article.license.p1
        
        ext_link = SubElement(self.license_p, "ext-link")
        ext_link.set("ext-link-type", "uri")
        ext_link.set("xlink:href", poa_article.license.href)
        ext_link.text = poa_article.license.name
        ext_link.tail = poa_article.license.p2

    def set_copyright(self, parent, poa_article):
        if len(poa_article.contributors) > 2:
            contributor = poa_article.contributors[0]
            copyright_holder = contributor.surname + " et al"
        elif len(poa_article.contributors) == 2:
            contributor1 = poa_article.contributors[0]
            contributor2 = poa_article.contributors[1]
            copyright_holder = contributor1.surname + " & " + contributor2.surname
        elif len(poa_article.contributors) == 1:
            contributor = poa_article.contributors[0]
            copyright_holder = contributor.surname
        else:
            copyright_holder = ""
            
        # copyright-statement
        copyright_year = ""
        date = poa_article.get_date("license")
        if not date:
            # if no license date specified, use the article accepted date
            date = poa_article.get_date("accepted")
        if date:
            copyright_year = date.date.tm_year
            
        copyright_statement = u'Copyright \u00a9 ' + str(copyright_year) + ", " + copyright_holder
        self.copyright_statement = SubElement(parent, "copyright-statement")
        self.copyright_statement.text = copyright_statement
        
        # copyright-year
        self.copyright_year = SubElement(parent, "copyright-year")
        self.copyright_year.text = str(copyright_year)
        
        # copyright-holder
        self.copyright_holder = SubElement(parent, "copyright_holder")
        self.copyright_holder.text = copyright_holder
    
    def set_permissions(self, parent, poa_article):
        self.permissions = SubElement(parent, "permissions")
        if poa_article.license.copyright is True:
            self.set_copyright(self.permissions, poa_article)
        self.set_license(self.permissions, poa_article)

    def set_contrib_group(self, parent, poa_article):
        self.contrib_group = SubElement(parent, "contrib-group")

        for contributor in poa_article.contributors:
            self.contrib = SubElement(self.contrib_group, "contrib")

            self.contrib.set("contrib-type", contributor.contrib_type)
            if contributor.corresp == True:
                self.contrib.set("corresp", "yes")
            if contributor.equal_contrib == True:
                self.contrib.set("equal_contrib", "yes")
            if contributor.auth_id:
                self.contrib.set("auth-id", contributor.auth_id)
                
            if contributor.collab:
                self.collab = SubElement(self.contrib, "collab")
                self.collab.text = contributor.collab
            else:
                self.name = SubElement(self.contrib, "name")
                self.surname = SubElement(self.name, "surname")
                self.surname.text = contributor.surname
                self.given_name = SubElement(self.name, "given-names")
                self.given_name.text = contributor.given_name

            if contributor.orcid:
                self.orcid = SubElement(self.contrib, "uri")
                self.orcid.set("content-type", "orcid")
                self.orcid.set("xlink:href", contributor.orcid)

            for affiliation in contributor.affiliations:
                self.aff = SubElement(self.contrib, "aff")

                if affiliation.department:
                    self.addline = SubElement(self.aff, "addr-line")
                    self.department = SubElement(self.addline, "named-content")
                    self.department.set("content-type", "department")
                    self.department.text = affiliation.department

                if affiliation.institution:
                    self.institution = SubElement(self.aff, "institution")
                    self.institution.text = affiliation.institution

                if affiliation.city:
                    self.addline = SubElement(self.aff, "addr-line")
                    self.city = SubElement(self.addline, "named-content")
                    self.city.set("content-type", "city")
                    self.city.text = affiliation.city

                if affiliation.country:
                    self.country = SubElement(self.aff, "country")
                    self.country.text = affiliation.country

                if affiliation.phone:
                    self.phone = SubElement(self.aff, "phone")
                    self.phone.text = affiliation.phone

                if affiliation.fax:
                    self.fax = SubElement(self.aff, "fax")
                    self.fax.text = affiliation.fax                    

                if affiliation.email:
                    self.email = SubElement(self.aff, "email")
                    self.email.text = affiliation.email

    def set_article_categories(self, parent, poa_article):
        # article-categories
        if poa_article.get_display_channel() or len(poa_article.article_categories) > 0:
            self.article_categories = SubElement(parent, "article-categories")
            
            if poa_article.get_display_channel():
                # subj-group subj-group-type="display-channel"
                subj_group = SubElement(self.article_categories, "subj-group")
                subj_group.set("subj-group-type", "display-channel")
                subject = SubElement(subj_group, "subject")
                subject.text = poa_article.get_display_channel()
            
            for article_category in poa_article.article_categories:
                # subj-group subj-group-type="heading"
                subj_group = SubElement(self.article_categories, "subj-group")
                subj_group.set("subj-group-type", "heading")
                subject = SubElement(subj_group, "subject")
                subject.text = article_category

    def set_pub_date(self, parent, poa_article, pub_type):
        # pub-date pub-type = pub_type
        date = poa_article.get_date(pub_type)
        if date:
            self.pub_date = SubElement(parent, "pub-date")
            self.pub_date.set("pub-type", pub_type)
            year = SubElement(self.pub_date, "year")
            year.text = str(date.date.tm_year)

    def set_date(self, parent, poa_article, date_type):
        # date date-type = date_type
        date = poa_article.get_date(date_type)
        if date:
           self.date = SubElement(parent, "date")
           self.date.set("date-type", date_type)
           day = SubElement(self.date, "day")
           day.text = str(date.date.tm_mday).zfill(2)
           month = SubElement(self.date, "month")
           month.text = str(date.date.tm_mon).zfill(2)
           year = SubElement(self.date, "year")
           year.text = str(date.date.tm_year)

    def set_history(self, parent, poa_article):
        self.history = SubElement(parent, "history")
        
        for date_type in self.date_types:
            date = poa_article.get_date(date_type)
            if date:
                self.set_date(self.history, poa_article, date_type)

    def printXML(self):
        print self.root

    def prettyXML(self):
        publicId = '-//NLM//DTD Journal Archiving and Interchange DTD v3.0 20080202//EN'
        systemId = 'http://dtd.nlm.nih.gov/archiving/3.0/archivearticle3.dtd'
        encoding = 'utf-8'
        namespaceURI = None
        qualifiedName = "article"
    
        doctype = minidom.DocumentType(qualifiedName)
        doctype._identified_mixin_init(publicId, systemId)

        rough_string = ElementTree.tostring(self.root, encoding)
        reparsed = minidom.parseString(rough_string)
        if doctype:
            reparsed.insertBefore(doctype, reparsed.documentElement)
        return reparsed.toprettyxml(indent="\t", encoding = encoding)

class ContributorAffiliation():
    phone = None
    fax = None
    email = None 

    department = None
    institution = None
    city = None 
    country = None

class eLifePOSContributor():
    """
    Currently we are not sure that we can get an auth_id for 
    all contributors, so this attribute remains an optional attribute. 
    """

    corresp = False
    equal_contrib = False

    auth_id = None
    orcid = None
    collab = None

    def __init__(self, contrib_type, surname, given_name, collab = None):
        self.contrib_type = contrib_type
        self.surname = surname
        self.given_name = given_name
        self.affiliations = []
        self.collab = collab

    def set_affiliation(self, affiliation):
        self.affiliations.append(affiliation)

class eLifeDate():
    """
    A struct_time date and a date_type
    """
    
    def __init__(self, date_type, date):
        self.date_type = date_type
        # Date as a time.struct_time
        self.date = date



class eLifeLicense():
    """
    License with some eLife preset values by license_id
    """
    
    license_id = None
    license_type = None
    copyright = False
    href = None
    name = None
    p1 = None
    p2 = None
    
    def __init__(self, license_id = None):
        if license_id:
            self.init_by_license_id(license_id)
        
    def init_by_license_id(self, license_id):
        """
        For license_id value, set the license properties
        """
        if int(license_id) == 1:
            self.license_id = license_id
            self.license_type = "open-access"
            self.copyright = True
            self.href = "http://creativecommons.org/licenses/by/3.0/"
            self.name = "Creative Commons Attribution License"
            self.p1 = "This article is distributed under the terms of the "
            self.p2 = ", which permits unrestricted use and redistribution provided that the original author and source are credited."
        elif int(license_id) == 2:
            self.license_id = license_id
            self.license_type = "open-access"
            self.copyright = False
            self.href = "http://creativecommons.org/publicdomain/zero/1.0/"
            self.name = "Creative Commons CC0"
            self.p1 = "This is an open-access article, free of all copyright, and may be freely reproduced, distributed, transmitted, modified, built upon, or otherwise used by anyone for any lawful purpose. The work is made available under the "
            self.p2 = " public domain dedication."

class eLifePOA():
    """
    We include some boiler plate in the init, namely articleType
    """
    contributors = [] 

    def __init__(self, doi, title):
        self.articleType = "research-article"
        self.doi = doi 
        self.contributors = [] 
        self.title = title 
        self.abstract = ""
        self.manuscript = None
        self.dates = None
        self.license = None
        self.article_categories = []

    def add_contributor(self, contributor):
        self.contributors.append(contributor)

    def add_date(self, date):
        if not self.dates:
            self.dates = {}
        self.dates[date.date_type] = date
        
    def get_date(self, date_type):
        try:
            return self.dates[date_type]
        except (KeyError, TypeError):
            return None
        
    def get_display_channel(self):
        # display-channel string relates to the articleType
        if self.articleType == "research-article":
            return "Research article"
        return None
    
    def add_article_category(self, article_category):
        self.article_categories.append(article_category)

def repl(m):
    # Convert hex to int to unicode character
    chr_code = int(m.group(1), 16)
    return unichr(chr_code)

def entity_to_unicode(s):
    """
    Quick convert unicode HTML entities to unicode characters
    using a regular expression replacement
    """
    s = re.sub(r"&#x(....);", repl, s)
    return s

if __name__ == '__main__':

    # test affiliations 
    aff1 = ContributorAffiliation()
    aff1.department = entity_to_unicode("Edit&#x00F3;ri&#x00E1;l Dep&#x00E1;rtment")
    aff1.institution = "eLife"
    aff1.city = "Cambridge"
    aff1.country = "UK"
    aff1.email = "m.harrsion@elifesciecnes.org"

    aff2 = ContributorAffiliation()
    aff2.department = entity_to_unicode("Coffe Ho&#x00FC;se")
    aff2.institution = "hipster"
    aff2.city = "London"
    aff2.country = "UK"
    aff2.email = "m.harrsion@elifesciecnes.org"

    aff3 = ContributorAffiliation()
    aff3.department = entity_to_unicode("Coffe Ho&#x00FC;se")
    aff3.institution = "hipster"
    aff3.city = "London"
    aff3.country = "UK"
    aff3.email = "i.mulvany@elifesciences.org"


    # test authors 
    auth1 = eLifePOSContributor("author", "Harrison", "Melissa")
    auth1.auth_id = "029323as"
    auth1.corresp = True
    auth1.orcid = "this is an orcid"
    auth1.set_affiliation(aff1)
    auth1.set_affiliation(aff2)

    auth2 = eLifePOSContributor("author", "Mulvany", "Ian")
    auth2.auth_id = "ANOTHER_ID_2"
    auth2.corresp = True
    auth2.set_affiliation(aff3)
    
    # group collab author
    auth3 = eLifePOSContributor("author", None, None, "eLife author group")
    auth3.auth_id = "groupAu1"

    # dates
    t = time.strptime("2013-10-03", "%Y-%m-%d")
    date_epub = eLifeDate("epub", t)
    date_accepted = eLifeDate("accepted", t)
    date_received = eLifeDate("received", t)
    # copyright date as the license date
    t_license = time.strptime("2013-10-03", "%Y-%m-%d")
    date_license = eLifeDate("license", t_license)
    license = eLifeLicense(1)

    # test article 
    doi = "http://dx.doi.org/10.7554/eLife.00929"
    title = "The Test Title"
    abstract = "Test abstract"
    newArticle = eLifePOA(doi, title)
    newArticle.abstract = abstract

    newArticle.add_contributor(auth1)
    newArticle.add_contributor(auth2)
    newArticle.add_contributor(auth3)
    
    newArticle.add_date(date_epub)
    newArticle.add_date(date_accepted)
    newArticle.add_date(date_received)
    newArticle.add_date(date_license)
    
    newArticle.license = license
    
    newArticle.add_article_category("Cell biology")

    # test the XML generator 
    eXML = eLife2XML(newArticle)
    prettyXML = eXML.prettyXML()
    print prettyXML



