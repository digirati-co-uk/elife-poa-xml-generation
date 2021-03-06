Feature: Generate POA XML
  In order to generate XML
  As a user
  I want to use the XML generation libraries

  Scenario: Check settings exist and their value
    Given I read settings <property>
    Then I have the value <value>
    
  Examples:
    | property                                    | value
    | ROWS_WITH_COLNAMES                          | 3
    | LESS_THAN_ESCAPE_SEQUENCE                   | LTLT
    | GREATER_THAN_ESCAPE_SEQUENCE                | GTGT

  Scenario: Override settings values
    Given I set settings <property> to <value>
    When I read settings <property>
    Then I have the value <value>
    
  Examples:
    | property                                    | value
    | LESS_THAN_ESCAPE_SEQUENCE                   | foo
    | XLS_PATH                                    | test_data/

  Scenario: Override json settings values
    Given I set json settings <property> to <value>
    When I read settings <property>
    Then I have the json value <value>
    
  Examples:
    | property                                    | value
    | XLS_FILES                                   | {"authors" : "poa_author.csv", "license" : "poa_license.csv", "manuscript" : "poa_manuscript.csv", "received" : "poa_received.csv", "subjects" : "poa_subject_area.csv", "organisms": "poa_research_organism.csv"}

  Scenario: Test entity to unicode conversion
    Given I have the raw string <string>
    When I convert the string with entities to unicode
    Then I have the unicode <unicode>

  Examples:
    | string                                      | unicode
    | muffins                                     | muffins
    | Coffe Ho&#x00FC;se                          | Coffe Hoüse
    | Edit&#x00F3;rial&#x00F3; Department&#x00F3; | Editórialó Departmentó
    
  Scenario: Angle bracket escape sequence conversion
    Given I reload settings
    And I have the raw string <string>
    When I decode the string with decode brackets
    Then I have the decoded string <decoded_string>
    
  Examples:
    | string                                      | decoded_string
    | LTLT                                        | <
    | GTGT                                        | >
    | LTLTGTGT                                    | <>
    | LTLTiGTGTeyeLTLT/iGTGT                      | <i>eye</i>
    | LTLTiGTGTNicotiana attenuataLTLT/iGTGT      | <i>Nicotiana attenuata</i>
    | YLTLTsupGTGT1LTLT/supGTGTSLTLTsupGTGT2LTLT/supGTGTPLTLTsupGTGT3LTLT/supGTGTTLTLTsupGTGT4LTLT/supGTGTSLTLTsupGTGT5LTLT/supGTGTPLTLTsupGTGT6LTLT/supGTGTSLTLTsupGTGT7LTLT/supGTGT repeats                         | Y<sup>1</sup>S<sup>2</sup>P<sup>3</sup>T<sup>4</sup>S<sup>5</sup>P<sup>6</sup>S<sup>7</sup> repeats
    
  Scenario: Parse CSV files
    Given I set settings XLS_PATH to test_data/
    And I set XLS_FILES to the default
    And I reload XML generation libraries
    And I have article_id <article_id>
    And I have author_id <author_id>
    When I set attribute to parseCSVFiles method <method_name>
    Then I have attribute <attribute>
    
  Examples:
    | article_id    | author_id  | method_name             | attribute
    | 00003         |            | get_title               | This, 'title, includes "quotation", marks & more ü
    | 00007         |            | get_title               | Herbivory-induced "volatiles" function as defenses increasing fitness of the native plant LTLTiGTGTNicotiana attenuataLTLT/iGTGT in nature
    | 00003         | 1258       | get_author_first_name   | Preetha
    | 00012         |            | get_license             | 1
    | 00007         |            | get_organisms           | Other
    | 00003         |            | get_organisms           | B. subtilis,D. melanogaster,E. coli,Mouse
    | 00007         |            | get_subjects            | Genomics and evolutionary biology,Plant biology
    | 00007         |            | get_abstract            | An abstract with some "quotation" marks
    | 00012         |            | get_abstract            | In this abstract are consensus YLTLTsupGTGT1LTLT/supGTGTSLTLTsupGTGT2LTLT/supGTGTPLTLTsupGTGT3LTLT/supGTGTTLTLTsupGTGT4LTLT/supGTGTSLTLTsupGTGT5LTLT/supGTGTPLTLTsupGTGT6LTLT/supGTGTSLTLTsupGTGT7LTLT/supGTGT repeats, LTLTiGTGTDrosophilaLTLT/iGTGT and "quotations".
    | 00003         |            | get_articleType         | 10
    | 00007         |            | get_articleType         | 1
    | 00012         |            | get_articleType         | 14
    | 00012         |            | get_group_authors       | 0
    | 02725         |            | get_group_authors       | order_start15order_endANECS111
    | 04969         |            | get_received_date       | " "
    | 04969         |            | get_receipt_date        | 2014-09-30 03:44:10.960
    
  Scenario: Escape unmatched angle brackets
    Given I have the raw string <string>
    And I copy string to world decoded string
    When I escape unmatched angle brackets
    I have the decoded string <decoded_string>
    
  Examples:
    | string                                           | decoded_string
    | cookies                                          | cookies
    | α beta                                           | α beta
    | <i> α < ü > i</i>                                | <i> α &lt; ü &gt; i</i>
    | <i> <<</i>                                       | <i> &lt;&lt;</i>
    | < <i></i>                                        | &lt; <i></i> 
    | <i><</i>                                         | <i>&lt;</i>
    | no < tag                                         | no &lt; tag  
    | <i>a</i> <                                       | <i>a</i> &lt;
    | <i><sup><</sup>></i>                             | <i><sup>&lt;</sup>&gt;</i>
    | <u><b><</b>></u>                                 | <u><b>&lt;</b>&gt;</u>
    
  Scenario: Test entity to unicode conversion, angle bracket replacements and XML tree building
    Given I have the raw string <string>
    And I convert the string with entities to unicode
    And I decode the string with decode brackets
    And I tag replace the decoded string
    And I escape unmatched angle brackets
    And I surround the decoded string with tag_name <tag_name>
    And I have the root xml element
    When I convert the decoded string to an xml element
    Then I have xml element string <xml_elem_string>
    And I append the xml element to the root xml element
    And I convert the root xml element to string
    Then I have the xml string <xml_string>

  Examples:
    | string                                           | tag_name  | xml_elem_string                                            | xml_string
    | muffins                                          | p         | <?xml version="1.0" ?><p>muffins</p>                       | <?xml version="1.0" ?><root><p>muffins</p></root>
    | Coffe LTLTiGTGTHo&#x00FC;seLTLT/iGTGT&#x03B1;    | p         | <?xml version="1.0" ?><p>Coffe <italic>Hoüse</italic>α</p>  | <?xml version="1.0" ?><root><p>Coffe <italic>Hoüse</italic>α</p></root>
    | C&#x00FC; LTLTiGTGTH&#x00FC;sLTLT/iGTGT&#x03B1; LTLTsupGTGTH&#x00FC;LTLT/supGTGTa    | p         | <?xml version="1.0" ?><p>Cü <italic>Hüs</italic>α <sup>Hü</sup>a</p>  | <?xml version="1.0" ?><root><p>Cü <italic>Hüs</italic>α <sup>Hü</sup>a</p></root>
    | I LTLTiGTGTLTLTsupGTGTmLTLT/supGTGTLTLT/iGTGT        | p         | <?xml version="1.0" ?><p>I <italic><sup>m</sup></italic></p>  | <?xml version="1.0" ?><root><p>I <italic><sup>m</sup></italic></p></root>
    | 2&#x00FC; LTLTiGTGTisLTLT/iGTGT LTLT 3LTLTsupGTGT&#x03B1;LTLT/supGTGT GTGT 4    | p         | <?xml version="1.0" ?><p>2ü <italic>is</italic> &lt; 3<sup>α</sup> &gt; 4</p>  | <?xml version="1.0" ?><root><p>2ü <italic>is</italic> &lt; 3<sup>α</sup> &gt; 4</p></root>
    | LTLTiGTGTSalmonellaLTLT/iGTGT Typhi and LTLTiGTGTSalmonellaLTLT/iGTGT Paratyphi  | p | <?xml version="1.0" ?><p><italic>Salmonella</italic> Typhi and <italic>Salmonella</italic> Paratyphi</p> | <?xml version="1.0" ?><root><p><italic>Salmonella</italic> Typhi and <italic>Salmonella</italic> Paratyphi</p></root>
    | renamed CpoB (LTLTuGTGTLTLTbGTGTCLTLT/bGTGTLTLT/uGTGToordinator of LTLTuGTGTLTLTbGTGTPLTLT/bGTGTLTLT/uGTGTG synthesis  | p | <?xml version="1.0" ?><p>renamed CpoB (<u><b>C</b></u>oordinator of <u><b>P</b></u>G synthesis</p> | <?xml version="1.0" ?><root><p>renamed CpoB (<u><b>C</b></u>oordinator of <u><b>P</b></u>G synthesis</p></root>
    
    
  Scenario: Parse group authors string
    Given I have the raw string <string>
    And I have as list index <index>
    When I parse group authors
    And I set attribute to attribute index <index>
    Then I have attribute <attribute>
    
  Examples:
    | string                            | index  | attribute
    | order_start15order_endANECS111    | 15     | ANECS
    | order_start34order_endICGC Breast Cancer Group1order_start35order_endICGC Chronic Myeloid Disorders Group2order_start36order_endICGC Prostate Cancer Group313  | 34     | ICGC Breast Cancer Group
    | order_start34order_endICGC Breast Cancer Group1order_start35order_endICGC Chronic Myeloid Disorders Group2order_start36order_endICGC Prostate Cancer Group313  | 35     | ICGC Chronic Myeloid Disorders Group
    | order_start34order_endICGC Breast Cancer Group1order_start35order_endICGC Chronic Myeloid Disorders Group2order_start36order_endICGC Prostate Cancer Group313  | 36     | ICGC Prostate Cancer Group
    
    
  Scenario: Build eLifePOA article object for article
    Given I set settings XLS_PATH to test_data/
    And I set XLS_FILES to the default
    And I reload XML generation libraries
    And I have article_id <article_id>
    When I build POA article for article
    And I have as list index <index>
    And I have sub property <subproperty>
    And I set attribute to article object property <property>
    Then I have attribute <attribute>
    
  Examples:
    | article_id     | property       | index    | subproperty   | attribute
    | 00003          | title          |          |               | This, 'title, includes "quotation", marks & more ü
    | 00003          | contributors   | 0        | surname       | Anand 
    | 02935          | contributors   | 0        | surname       | Ju
    | 02935          | contributors   | 32       | surname       | Malkin
    | 02935          | contributors   | 33       | collab        | ICGC Breast Cancer Group
    | 02935          | contributors   | 34       | collab        | ICGC Chronic Myeloid Disorders Group
    | 02935          | contributors   | 35       | collab        | ICGC Prostate Cancer Group
    | 02935          | contributors   | 36       | surname       | Foster
    | 02935          | is_poa         |          |               | True
    
        
  Scenario: Build POA XML for article
    Given I set settings XLS_PATH to test_data/
    And I set settings TARGET_OUTPUT_DIR to test_output/
    And I set XLS_FILES to the default
    And I reload XML generation libraries
    And I have article_id <article_id>
    When I build POA XML for article
    Then I have attribute <attribute>
    
  Examples:
    | article_id     | attribute
    | 00003          | True
    | 02935          | True
    | 99999          | False