from generatePoaXml import *
from parseXlsFiles import * 
import xlrd


"""
read from an xls file
output an xml file


# Gotchas
TODO: currnet XLS does not provide author contrib type TODO: query for author contrib type 
TODO: we need a decision on what we do with middle names, for now we are ignoring them 
TODO: print out authors in their contrib order 
TODO: add contrib-type
TODO: add managing editor information 
TODO: add subjects 

"""

def build_xml_for_article(article_id):
	doi = get_doi(article_id)
	title = get_title(article_id)
	uri = doi2uri(doi)
	article = eLifePOA(uri, title)
	#
	abstract = get_abstract(article_id)
	article.abstract = abstract
	#
	licence_id = get_licence(article_id)
	license = eLifeLicense(licence_id)
	article.license = license
	#
	accepted_date = get_accepted_date(article_id)

	t_accepted = time.strptime(accepted_date.split()[0], "%Y-%m-%d")
	accepted = eLifeDate("accepted", t_accepted)
	article.add_date(accepted)
	#
	# set the licence date to be the same as the accepted date
	date_license = eLifeDate("license", t_accepted)
	article.add_date(date_license)

	# categories
	categories = get_subjects(article_id)
	for category in categories:
		article.add_article_category(category)

	# research organisim
	research_organisims = get_organisims(article_id)
	for research_organisim in research_organisims:
		article.add_research_organism(research_organisim)

	# author information 
	author_ids = get_author_ids(article_id)
	for author_id in author_ids:

		# create affilication infromation for author, need to know 
		# if they are corresponding or not 
		department = get_author_department(article_id, author_id)
		institution = get_author_organisation(article_id, author_id)
		country = get_author_country(article_id, author_id)
		city = get_author_city(article_id, author_id)
		email = get_author_email(article_id, author_id)

		affiliation = ContributorAffiliation()
		affiliation.department = department
		affiliation.institution = institution
		affiliation.city = city
		affiliation.country = country
		affiliation.email = email 

		contrib_type = get_author_contrib_type(article_id, author_id)
		first_name = get_author_first_name(article_id, author_id)			
		last_name = get_author_last_name(article_id, author_id)	

		author = eLifePOSContributor(contrib_type, last_name, first_name)		
		author.auth_id = `int(author_id)`
		author.corresp = True
		author.set_affiliation(affiliation)

		article.add_contributor(author)


	article_xml = eLife2XML(article)
	return article_xml


if __name__ == "__main__":
	# get a list of active article numbers 
	article_ids = index_manuscript_on_article_id().keys()

	for article_id in article_ids:
		try: 
			xml = build_xml_for_article(article_id)
			print "xml built for ", article_id
			# print xml.prettyXML()
		except:
			print "xml build failed for", article_id
 