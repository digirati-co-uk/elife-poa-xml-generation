import xml
from xml.dom.minidom import Document
from collections import namedtuple
from xml.etree.ElementTree import Element, SubElement, Comment, tostring
from xml.etree import ElementTree
from xml.dom import minidom
import time
import calendar
import re
import os
from git import *
from generatePoaXml import *
from xml_generation import *
from parsePoaXml import *
import settings

"""

"""

class pubMedPoaXML(object):
    """
    Generate PubMed XML for the PoA article, which is pubstatus = "aheadofprint"
    """
    def __init__(self, poa_articles, pub_date = None):
        """
        set the root node
        get the article type from the object passed in to the class
        set default values for items that are boilder plate for this XML 
        """
        self.root = Element('ArticleSet')

        # set the boiler plate values
        self.contrib_types = ["author"]
        self.date_types = ["received", "accepted"]
        self.elife_journal_title = "eLife"
        self.elife_epub_issn = "2050-084X"
        self.elife_publisher_name = "eLife Sciences Publications Limited"
        self.elife_language = "EN"
        self.elife_journal_volume = "3"
        self.elife_journal_issue = ""

        # Publication date
        if pub_date is None:
            self.pub_date = time.gmtime()

        # Generate batch id
        self.elife_doi_batch_id = "elife-" + time.strftime("%Y-%m-%d-%H%M%S", self.pub_date) + "-PubMed"

        # set comment
        generated = time.strftime("%Y-%m-%d %H:%M:%S")
        last_commit = get_last_commit_to_master()
        comment = Comment('generated by eLife at ' + generated + ' from version ' + last_commit)
        self.root.append(comment)

        self.build(self.root, poa_articles)

    def build(self, root, poa_articles):
        
        for poa_article in poa_articles:
            self.article = SubElement(root, "Article")
            self.set_journal(self.article, poa_article)
            self.set_replaces(self.article, poa_article)
            self.set_article_title(self.article, poa_article)
            self.set_e_location_id(self.article, poa_article)
            self.set_language(self.article, poa_article)
            self.set_author_list(self.article, poa_article)
            self.set_article_id_list(self.article, poa_article)
            self.set_history(self.article, poa_article)
            self.set_abstract(self.article, poa_article)
            self.set_object_list(self.article, poa_article)

    def get_pub_type(self, poa_article):
        """
        Given an article object, determine whether the pub_type is for
        PoA article or VoR article
        """
        
        pub_type = None
        if poa_article.is_poa() is False:
            # VoR
            pub_type = "epublish"
        elif poa_article.is_poa() is True:
            # PoA
            pub_type = "aheadofprint"
        return pub_type

    def set_journal(self, parent, poa_article):
        self.journal = SubElement(parent, "Journal")
        
        self.publisher_name = SubElement(self.journal, "PublisherName")
        self.publisher_name.text = self.elife_publisher_name

        self.journal_title = SubElement(self.journal, 'JournalTitle')
        self.journal_title.text = self.elife_journal_title
        
        self.issn = SubElement(self.journal, 'Issn')
        self.issn.text = self.elife_epub_issn
        
        self.volume = SubElement(self.journal, "Volume")
        self.volume.text = self.elife_journal_volume

        self.issue = SubElement(self.journal, "Issue")
        self.issue.text = self.elife_journal_issue
        
        #self.journal_pubdate = SubElement(self.journal, "PubDate")
        pub_type = self.get_pub_type(poa_article)
        if pub_type == "epublish":
            a_date = poa_article.get_date("epub").date
        else:
            a_date = self.pub_date
        self.set_pub_date(self.journal, a_date, pub_type)

    def set_replaces(self, parent, poa_article):
        """
        Set the Replaces tag, if applicable
        """
        # If the article is VoR and is was ever PoA
        if poa_article.is_poa() is False and poa_article.was_ever_poa is True:
            self.replaces = SubElement(parent, 'Replaces')
            self.replaces.set("IdType", "doi")
            self.replaces.text = poa_article.doi

    def set_article_title(self, parent, poa_article):
        """
        Set the titles and title tags allowing sub tags within title
        """
        tag_name = 'ArticleTitle'
        # Pubmed allows <i> tags, not <italic> tags
        tag_converted_title = replace_tags(poa_article.title, 'italic', 'i')
        tagged_string = '<' + tag_name + '>' + tag_converted_title + '</' + tag_name + '>'
        reparsed = minidom.parseString(tagged_string)

        root_xml_element = append_minidom_xml_to_elementtree_xml(
            parent, reparsed
        )
        
    def set_e_location_id(self, parent, poa_article):
        self.e_location_id = SubElement(parent, "ELocationID")
        self.e_location_id.set("EIdType", "doi")
        self.e_location_id.text = poa_article.doi

    def set_language(self, parent, poa_article):
        self.language = SubElement(parent, "Language")
        self.language.text = self.elife_language

    def set_author_list(self, parent, poa_article, contrib_type = None):
        # If contrib_type is None, all contributors will be added regardless of their type
        self.contributors = SubElement(parent, "AuthorList")

        for contributor in poa_article.contributors:
            if contrib_type:
                # Filter by contrib_type if supplied
                if contributor.contrib_type != contrib_type:
                    continue
            # Skip contributors with no surname and no collab
            if  (contributor.surname == "" or contributor.surname is None) \
            and (contributor.collab == "" or contributor.collab is None):
                continue
                
            self.person_name = SubElement(self.contributors, "Author")
  
            if contributor.given_name:
                self.given_name = SubElement(self.person_name, "FirstName")
                self.given_name.text = contributor.given_name
            
            if contributor.surname:
                self.surname = SubElement(self.person_name, "LastName")
                self.surname.text = contributor.surname
            
            if contributor.collab:
                self.collective_name = SubElement(self.person_name, "CollectiveName")
                self.collective_name.text = contributor.collab
            
            # Only add one affiliation per author for Pubmed
            for aff in contributor.affiliations[:1]:
                self.affiliation = SubElement(self.person_name, "Affiliation")
                self.affiliation.text = aff
                
            if contributor.orcid:
                self.orcid = SubElement(self.person_name, "Identifier")
                self.orcid.set("Source", "ORCID")
                self.orcid.text = contributor.orcid

    def set_article_id_list(self, parent, poa_article):
        self.article_id_list = SubElement(parent, "ArticleIdList")
        self.article_id = SubElement(self.article_id_list, "ArticleId")
        self.article_id.set("IdType", "doi")
        self.article_id.text = poa_article.doi

    def set_pub_date(self, parent, pub_date, pub_type):
        if pub_date:
            self.publication_date = SubElement(parent, "PubDate")
            self.publication_date.set("PubStatus", pub_type)
            year = SubElement(self.publication_date, "Year")
            year.text = str(pub_date.tm_year)
            month = SubElement(self.publication_date, "Month")
            # Get full text name of month
            month.text = time.strftime('%B', pub_date)
            day = SubElement(self.publication_date, "Day")
            day.text = str(pub_date.tm_mday).zfill(2)

    def set_date(self, parent, a_date, date_type):
        if a_date:
           self.date = SubElement(parent, "PubDate")
           self.date.set("PubStatus", date_type)
           year = SubElement(self.date, "Year")
           year.text = str(a_date.tm_year)
           month = SubElement(self.date, "Month")
           month.text = str(a_date.tm_mon).zfill(2)
           day = SubElement(self.date, "Day")
           day.text = str(a_date.tm_mday).zfill(2)

    def set_history(self, parent, poa_article):
        self.history = SubElement(parent, "History")
        
        for date_type in self.date_types:
            date = poa_article.get_date(date_type)
            if date:
                self.set_date(self.history, date.date, date_type)
                
        # If the article is VoR and is was ever PoA, then set the aheadofprint history date
        if poa_article.is_poa() is False and poa_article.was_ever_poa is True:
            date_value_type = "epub"
            date_type = "aheadofprint"
            date = poa_article.get_date(date_value_type)
            if date:
                self.set_date(self.history, date.date, date_type)
                
    def set_abstract(self, parent, poa_article):

        tag_name = 'Abstract'
        # Pubmed allows <i> tags, not <italic> tags
        tag_converted_abstract = replace_tags(poa_article.abstract, 'italic', 'i')
        tagged_string = '<' + tag_name + '>' + tag_converted_abstract + '</' + tag_name + '>'
        reparsed = minidom.parseString(tagged_string)

        root_xml_element = append_minidom_xml_to_elementtree_xml(
            parent, reparsed
        )

    def set_object_list(self, parent, poa_article):
        # Keywords and others go in Object tags
        self.object_list = SubElement(parent, "ObjectList")
        
        # Add research organisms
        for research_organism in poa_article.research_organisms:
            if research_organism.lower() != 'other':
                self.set_object(self.object_list, "keyword", "value", research_organism.lower())
        
        # Add article categories
        for article_category in poa_article.article_categories:
            # Break on "and" and capitalise the first letter
            categories = article_category.split('and')
            for category in categories:
                category = category.strip().lower()
                self.set_object(self.object_list, "keyword", "value", category)
                
        # Add keywords
        for keyword in poa_article.author_keywords:
            self.set_object(self.object_list, "keyword", "value", keyword)
                
        # Finally, do not leave an empty ObjectList tag, if present
        if len(self.object_list) <= 0:
            parent.remove(self.object_list)
        
    def set_object(self, parent, object_type, param_name, param):
        # e.g.  <Object Type="keyword"><Param Name="value">human</Param></Object>
        self.object = SubElement(parent, "Object")
        self.object.set("Type", object_type)
        self.param= SubElement(self.object, "Param")
        self.param.set("Name", param_name)
        self.param.text = param

    def printXML(self):
        print self.root

    def prettyXML(self):
        publicId = '-//NLM//DTD PubMed 2.6//EN'
        systemId = 'http://www.ncbi.nlm.nih.gov:80/entrez/query/static/PubMed.dtd'
        encoding = 'utf-8'
        namespaceURI = None
        qualifiedName = "ArticleSet"

        doctype = ElifeDocumentType(qualifiedName)
        doctype._identified_mixin_init(publicId, systemId)

        rough_string = ElementTree.tostring(self.root, encoding)
        reparsed = minidom.parseString(rough_string)
        if doctype:
            reparsed.insertBefore(doctype, reparsed.documentElement)

        #return reparsed.toprettyxml(indent="\t", encoding = encoding)
        return reparsed.toxml(encoding = encoding)

def build_pubmed_xml_for_articles(poa_articles):
    """
    Given a list of article article objects,
    and then generate pubmed XML from them
    """
    
    # test the XML generator 
    eXML = pubMedPoaXML(poa_articles)
    prettyXML = eXML.prettyXML()
    
    # Write to file
    f = open(settings.TMP_DIR + os.sep + eXML.elife_doi_batch_id + '.xml', "wb")
    f.write(prettyXML)
    f.close()
    
    print prettyXML

if __name__ == '__main__':
    
    article_xmls = [#"generated_xml_output/elife_poa_e03011.xml"
                    #,"generated_xml_output/elife_poa_e03198.xml"
                    #,"generated_xml_output/elife_poa_e03191.xml"
                    #,"generated_xml_output/elife_poa_e03300.xml"
                    #,"generated_xml_output/elife_poa_e02676.xml"
                    #,"generated_xml_output/elife02866.xml"
                    #,"generated_xml_output/elife02619.xml"
                    #,"generated_xml_output/elife02725.xml"
                    #,"generated_xml_output/elife04024.xml"
                    #,"generated_xml_output/elife_poa_e03528-mock-VoR.xml"
                    #,"generated_xml_output/elife01123.xml"
                    "generated_xml_output/elife03656.xml"
                    ,"generated_xml_output/elife03245.xml"
                    ,"generated_xml_output/elife_poa_e03126-mock-VoR.xml"
                    ,"generated_xml_output/elife_poa_e03674-mock-VoR.xml"
                    ,"generated_xml_output/elife_poa_e03125.xml"
                    ,"generated_xml_output/elife_poa_e03467.xml"
                    ]
    
    poa_articles = build_articles_from_article_xmls(article_xmls)
    
    # Pretend an article object was PoA'ed for testing
    for article in poa_articles:
        if (article.doi == '10.7554/eLife.03528'
            or article.doi == '10.7554/eLife.03126'
            or article.doi == '10.7554/eLife.03674'):
            article.was_ever_poa = True
    
    build_pubmed_xml_for_articles(poa_articles)






