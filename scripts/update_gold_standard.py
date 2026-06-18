import json, csv

with open('docs/news.json', encoding='utf-8') as f:
    articles = json.load(f)

with open('v2/data/gold_standard_annotations.csv', encoding='utf-8', newline='') as f:
    reader = csv.DictReader(f)
    existing_rows = list(reader)
    fieldnames = list(existing_rows[0].keys())

existing_urls = {r['url'] for r in existing_rows}
new_articles = [a for a in articles if a['url'] not in existing_urls]

# [valid, event_type, event_subtype, species_common, species_scientific, species_iucn,
#  animal_count, correct_place, correct_lat, correct_lon, loc_precision,
#  loc_correct, loc_error_type, human_cas, human_inj, animal_cas, severity, cluster_id, notes]
annotations = [
  # 1 Rajasthan AI surveillance tiger reserves
  ["YES","conservation_action","tech_deployment","Tiger","Panthera tigris","EN","","Rajasthan","27.0238","74.2179","state","YES","","0","0","0","low","","VALIDATE: Which tiger reserves specifically? Ranthambore, Sariska, Mukundra Hills all in Rajasthan."],
  # 2 NTPC solar project near flamingo habitat
  ["YES","habitat_threat","industrial_project","Greater Flamingo","Phoenicopterus roseus","LC","","Little Rann of Kutch","23.2","71.8","landscape","NO","too_broad","0","0","0","high","","NTPC 4500-acre solar project near flamingo breeding habitat. v1 pinned to Gujarat state centroid. VALIDATE: Exact project location near Little Rann of Kutch?"],
  # 3 Tiger takes over Raisen Fort Hill
  ["YES","sighting","wildlife_presence","Tiger","Panthera tigris","EN","1","Raisen","23.3325","77.7862","district","NO","too_broad","0","0","0","medium","","Tiger occupying Raisen Fort Hill, tourist entry shut. v1 pinned to MP state centroid. Correct place is Raisen district."],
  # 4 Bhopal lone-wolf attacks (FALSE POSITIVE)
  ["NO","other","","","","","","Bhopal","23.2599","77.4126","city","YES","","0","0","0","","","FALSE POSITIVE - terrorism/criminal arrest, not wildlife news."],
  # 5 Disease did not kill lions heat did Gujarat FM
  ["YES","mortality","heat_stress","Asiatic Lion","Panthera leo persica","EN","","Gir Forest National Park","21.1239","70.798","protected_area","NO","too_broad","0","0","0","high","GIR-LION-CUBS","v1 pinned to Gujarat state centroid. Correct location is Gir Forest NP. Part of GIR-LION-CUBS cluster."],
  # 6 Woman mauled to death by leopard Uttarakhand
  ["YES","hwc","leopard_attack","Leopard","Panthera pardus","VU","1","Uttarakhand","30.0668","79.0193","state","NO","too_broad","1","0","1","critical","","Woman killed by leopard, leopard shot dead. v1 state centroid. VALIDATE: Which district in Uttarakhand?"],
  # 7 8 Asiatic Lion cubs Gir died heat not infection
  ["YES","mortality","heat_stress","Asiatic Lion","Panthera leo persica","EN","8","Gir Forest National Park","21.1239","70.798","protected_area","NO","species_as_location","0","0","8","critical","GIR-LION-CUBS","NER captured 'Asiatic lion' as place_name again (same bug as GS078). Coords correct for Gir. Part of GIR-LION-CUBS cluster."],
  # 8 Forest dept World Environment Day Jharkhand
  ["YES","conservation_action","awareness_event","","","","","Jharkhand","23.6102","85.2799","state","YES","","0","0","0","low","","Borderline article. Forest dept World Environment Day cleanliness drive. State level correct."],
  # 9 Tiger carcass found Kaziranga
  ["YES","mortality","found_dead","Tiger","Panthera tigris","EN","1","Kaziranga National Park","26.5775","93.1711","protected_area","NO","too_broad","0","0","1","critical","","v1 pinned to Assam state centroid. Correct is Kaziranga NP. 5th big cat fatality this year. VALIDATE: Cause of death?"],
  # 10 Western Ghats high odonate endemism
  ["YES","research","biodiversity_survey","Odonata","","","","Western Ghats","13.0","75.5","region","YES","","0","0","0","low","","Research on dragonfly/damselfly endemism in Western Ghats. v1 location correct."],
  # 11 Assam school students water quality testing (FALSE POSITIVE)
  ["NO","other","","","","","","Assam","26.2006","92.9376","state","YES","","0","0","0","","","FALSE POSITIVE - school education program on water quality testing, not wildlife news."],
  # 12 Two new spider species Nagaland
  ["YES","discovery","new_species","Spider","","","2","Nagaland","26.1584","94.5624","state","YES","","0","0","0","low","","New spider species discovery from Nagaland. VALIDATE: Scientific names?"],
  # 13 Assam hidden Bunting roosts
  ["YES","research","conservation_ecology","Bunting","","","","Assam","26.2006","92.9376","state","YES","","0","0","0","medium","","Research on hidden Bunting roost sites key to species survival. VALIDATE: Which Bunting species?"],
  # 14 Kaziranga crackdown 3 poachers held
  ["YES","poaching","arrest","","","","","Kaziranga National Park","26.5775","93.1711","protected_area","NO","too_broad","0","0","0","high","","3 suspected poachers arrested at Kaziranga with weapons. v1 too broad (Assam state). VALIDATE: Target species (likely rhino)?"],
  # 15 Pawan Kalyan backs Peacock Tarantula conservation
  ["YES","conservation_action","political_endorsement","Peacock Tarantula","Poecilotheria metallica","CR","","Eastern Ghats","15.0","80.0","region","YES","","0","0","0","medium","","Critically Endangered Peacock Tarantula, Andhra CM Pawan Kalyan backing conservation. Eastern Ghats correct."],
  # 16 Rare dragonfly resurfaces Raimona 36 years
  ["YES","discovery","rediscovery","","","","","Raimona National Park","26.55","90.0","protected_area","NO","too_broad","0","0","0","medium","RAIMONA-DISCOVERY","Dragonfly not recorded for 36 years, rediscovered in Raimona NP. v1 too broad (Assam state). VALIDATE: Which dragonfly species?"],
  # 17 New gecko species Raimona
  ["YES","discovery","new_species","Gecko","","","","Raimona National Park","26.55","90.0","protected_area","NO","too_broad","0","0","0","low","RAIMONA-DISCOVERY","New gecko species from Raimona landscape. v1 too broad. Cluster with dragonfly rediscovery article."],
  # 18 40 ex-civil servants urge Assam forest force poll duty
  ["YES","policy","advocacy","","","","","Assam","26.2006","92.9376","state","YES","","0","0","0","medium","","Ex-civil servants opposing use of forest force for election duty. Affects wildlife protection capacity."],
  # 19 Northeast bat populations severe threat
  ["YES","research","population_threat","Bat","","","","Northeast India","25.2744","92.9376","region","YES","","0","0","0","high","","Multiple bat species under severe threat in Northeast India. Region level correct."],
  # 20 Assam villagers resist excavation flood mitigation
  ["YES","habitat_threat","infrastructure","","","","","Assam","26.2006","92.9376","state","YES","","0","0","0","medium","","Villagers resisting excavation for flood mitigation project. VALIDATE: Is this near a wildlife corridor?"],
  # 21 Wild elephant rampage Manikpur Guwahati
  ["YES","hwc","elephant_rampage","Asian Elephant","Elephas maximus","EN","","Manikpur, Guwahati","26.1445","91.7362","city","YES","","0","0","0","high","","Elephant rampage in Manikpur village near Guwahati. Families escaped. Location correct."],
  # 22 Woolly Bat found Khasi Hills first time India
  ["YES","discovery","first_india_record","Woolly Bat","","","","Khasi Hills, Meghalaya","25.5","91.8","landscape","NO","wrong_location","0","0","0","medium","","v1 captured Guwahati (Assam) but article is about Khasi Hills (Meghalaya). Different state. First India record."],
  # 23 INTERPOL wildlife trafficker Sikkim (likely duplicate of GS112)
  ["YES","poaching","trafficking_arrest","","","","","Sikkim","27.533","88.5122","state","YES","","0","0","0","critical","DUPLICATE-GS112","POTENTIAL DUPLICATE of GS112 - same headline, different Google News URL. Confirm if same article."],
  # 24 India to get cheetahs from Botswana (garbled RSS)
  ["YES","policy","species_reintroduction","Cheetah","Acinonyx jubatus","VU","","Kuno National Park","26.7","77.7","protected_area","NO","wrong_location","0","0","0","medium","","GARBLED RSS HEADLINE - multiple stories combined. Cheetah-from-Botswana is valid. Correct location is Kuno NP MP. v1 pinned to Bihar (wrong)."],
  # 25 Karnataka CM warns against killing wildlife
  ["YES","policy","political_statement","","","","","Karnataka","15.3173","75.7139","state","YES","","0","0","0","low","","CM Siddaramaiah warning against wildlife killing. Political statement. State level correct."],
  # 26 Wild elephants Tamil Nadu population 3170
  ["YES","research","population_census","Asian Elephant","Elephas maximus","EN","3170","Tamil Nadu","11.1271","78.6569","state","YES","","0","0","0","low","","Tamil Nadu elephant census 2025: 3,170 elephants. State centroid appropriate."],
  # 27 104 turtle hatchlings released rhino habitat Assam
  ["YES","conservation_action","captive_release","","","","104","Assam","26.2006","92.9376","state","YES","","0","0","0","low","","104 turtle hatchlings raised in temple pond released into rhino habitat. VALIDATE: Which turtle species? Specific release location?"],
  # 28 Tiger skin deer hides seized Guwahati godman
  ["YES","poaching","seizure_arrest","Tiger","Panthera tigris","EN","","Guwahati","26.1445","91.7362","city","YES","","0","0","1","critical","","Complete tiger skin and deer hides seized in Guwahati. Self-styled godman arrested. Location correct."],
  # 29 Grasslands Manas NP shrunk 50% three decades
  ["YES","habitat_threat","habitat_loss","","","","","Manas National Park","26.65","91.0","protected_area","YES","","0","0","0","critical","","50% grassland loss in Manas NP over 30 years per Field Director. Critical for corridor integrity analysis. v1 correct."],
  # 30 Mystery deaths Satpura Tiger Reserve NDTV
  ["YES","mortality","suspected_lapses","Tiger","Panthera tigris","EN","","Satpura Tiger Reserve","22.5167","78.2167","protected_area","YES","","0","0","0","critical","","Mystery animal deaths at Satpura TR. Letter alleges management lapses. v1 location correct."],
  # 31 Tiger count rises Orang Assam
  ["YES","research","population_census","Tiger","Panthera tigris","EN","","Orang National Park","26.5","92.0","protected_area","NO","too_broad","0","0","0","low","","Tiger count rising at Orang NP, expansion planned. v1 pinned to Assam state centroid. VALIDATE: Exact tiger count?"],
  # 32 Kerala seeks amend Wildlife Act allow killing
  ["YES","policy","wildlife_act_amendment","","","","","Kerala","10.8505","76.2711","state","YES","","0","0","0","high","","Controversial: Kerala seeking to amend Wildlife Protection Act to permit culling of problem animals. State level correct."],
  # 33 Kaziranga record tourists
  ["YES","research","tourism_report","","","","","Kaziranga National Park","26.5775","93.1711","protected_area","YES","","0","0","0","low","","Record tourist numbers at Kaziranga NP. Borderline article. v1 location correct."],
  # 34 Star Cement rebuild Kaziranga watch towers
  ["YES","conservation_action","infrastructure_restoration","","","","","Kaziranga National Park","26.5775","93.1711","protected_area","NO","too_broad","0","0","0","low","","Star Cement CSR: rebuilding watch towers in Kaziranga. v1 pinned to Assam state centroid."],
  # 35 Missing tusks elephant skeleton Bhadra TR
  ["YES","poaching","ivory_theft","Asian Elephant","Elephas maximus","EN","","Bhadra Tiger Reserve","13.6667","75.6333","protected_area","YES","","0","0","1","critical","","Tusks missing from elephant skeleton in Bhadra TR. Forest dept under scrutiny. v1 location correct."],
  # 36 Resorts TN highways Assam hurdles for elephants
  ["YES","habitat_threat","corridor_obstruction","Asian Elephant","Elephas maximus","EN","","Tamil Nadu","11.1271","78.6569","state","YES","","0","0","0","high","","Multi-state piece on elephant corridor obstructions. State level appropriate given multi-state scope."],
  # 37 New wildlife era Dibrugarh Zoological Park
  ["YES","conservation_action","zoo_development","","","","","Dibrugarh","27.4728","94.912","city","YES","","0","0","0","low","","Dibrugarh Zoo expansion. Borderline - captive wildlife not wild. VALIDATE: Include zoo articles in dataset?"],
  # 38 Mangroves to montane forests West Bengal ecology
  ["YES","research","ecological_survey","","","","","West Bengal","22.9868","87.855","state","YES","","0","0","0","low","","Feature on West Bengal forest ecosystems. State level appropriate."],
  # 39 Parbati Barua Padma Shri elephant mahout Assam
  ["YES","conservation_action","award_recognition","Asian Elephant","Elephas maximus","EN","","Assam","26.2006","92.9376","state","YES","","0","0","0","low","","Parbati Barua - famous elephant mahout from Assam - Padma Shri. Conservation recognition story."],
  # 40 One person killed man-animal conflict Karnataka per week (likely duplicate of GS113)
  ["YES","research","hwc_statistics","","","","","Karnataka","15.3173","75.7139","state","YES","","1","0","0","critical","DUPLICATE-GS113","POTENTIAL DUPLICATE of GS113 - same headline, different Google News URL. Confirm if same article."],
  # 41 Guardian of Wild Kaziranga first woman director
  ["YES","conservation_action","human_interest","","","","","Kaziranga National Park","26.5775","93.1711","protected_area","NO","too_broad","0","0","0","low","","Profile of first woman director of Kaziranga NP. v1 pinned to Assam state centroid."],
  # 42 Dubious business trading carbon India forests
  ["YES","policy","carbon_markets","","","","","India","22.5","82.0","state","NO","wrong_location","0","0","0","medium","","Investigative piece on carbon trading impact on Indian forests. v1 pinned to Andhra Pradesh (wrong - article is national in scope)."],
  # 43 MM Hills safari Mysuru wildlife tourism
  ["YES","conservation_action","ecotourism","","","","","MM Hills Wildlife Sanctuary","12.0","77.5","protected_area","NO","too_broad","0","0","0","low","","MM Hills WLS added to Mysuru tourism circuit. v1 pinned to Mysuru city, should be MM Hills WLS."],
  # 44 PM Modi visit Bandipur Tiger Reserve
  ["YES","conservation_action","political_visit","Tiger","Panthera tigris","EN","","Bandipur Tiger Reserve","11.6667","76.6333","protected_area","YES","","0","0","0","low","","PM Modi visit to Bandipur TR. High-profile conservation messaging. v1 location correct."],
  # 45 Indo-French project Kaziranga NP
  ["YES","conservation_action","international_collaboration","","","","","Kaziranga National Park","26.5775","93.1711","protected_area","YES","","0","0","0","low","","Indo-French conservation project at Kaziranga NP. v1 location correct."],
  # 46 300 Blackbucks roam Karnataka villages (likely duplicate of GS114)
  ["YES","sighting","mass_sighting","Blackbuck","Antilope cervicapra","NT","300","Karnataka","15.3173","75.7139","state","NO","too_broad","0","0","0","medium","DUPLICATE-GS114","POTENTIAL DUPLICATE of GS114 - same headline, different Google News URL. VALIDATE: Which Karnataka villages?"],
  # 47 Katarniaghat WLS tigress rescued 55 days
  ["YES","conservation_action","rescue_operation","Tiger","Panthera tigris","EN","1","Katarniaghat Wildlife Sanctuary","28.1","81.3","protected_area","YES","","0","0","0","medium","","55-day search for tigress finally rescued at Katarniaghat WLS. v1 location correct."],
  # 48 One rhino poached Assam 2021 lowest 21 years
  ["YES","research","annual_poaching_statistics","Indian One-horned Rhinoceros","Rhinoceros unicornis","VU","1","Assam","26.2006","92.9376","state","YES","","0","0","1","high","","Annual rhino poaching stats 2021: just 1 poached - record low in 21 years. Conservation success."],
  # 49 Assam plans add 4.52 sq km Kaziranga highlands
  ["YES","policy","PA_expansion","","","","","Kaziranga National Park","26.5775","93.1711","protected_area","NO","too_broad","0","0","0","medium","","Kaziranga expansion to protect flood refuge highlands. v1 pinned to Assam state centroid."],
  # 50 Baby elephant reunited mother Mudumalai
  ["YES","conservation_action","rescue_reunion","Asian Elephant","Elephas maximus","EN","1","Mudumalai National Park","11.55","76.6167","protected_area","YES","","0","0","0","medium","","Baby elephant rescued and reunited with mother at Mudumalai NP. v1 location correct."],
  # 51 Dia Mirza helicopter tourism Kaziranga
  ["YES","policy","advocacy","","","","","Kaziranga National Park","26.5775","93.1711","protected_area","NO","too_broad","0","0","0","medium","","Dia Mirza opposing helicopter tourism in Kaziranga. v1 pinned to Assam state centroid."],
  # 52 Assam flood Brahmaputra wildlife toll
  ["YES","habitat_threat","flood","","","","","Brahmaputra, Assam","26.8","93.7","region","YES","","0","0","0","critical","BRAHMAPUTRA-FLOOD-2020","Annual Brahmaputra floods taking heavy toll on Assam wildlife. Part of BRAHMAPUTRA-FLOOD-2020 cluster."],
  # 53 Why Kaziranga cannot survive without annual floods
  ["YES","research","flood_ecology","","","","","Kaziranga National Park","26.5775","93.1711","protected_area","YES","","0","0","0","high","BRAHMAPUTRA-FLOOD-2020","Paradox of floods at Kaziranga: ecologically necessary but kills animals. Part of BRAHMAPUTRA-FLOOD-2020 cluster."],
  # 54 Tortoises Anamalai forests Ganesan
  ["YES","conservation_action","community_conservation","Tortoise","","","","Anamalai Tiger Reserve","10.3667","77.0","protected_area","YES","","0","0","0","low","","Community conservationist tracking tortoises in Anamalai forests. v1 location correct."],
  # 55 Periyar Tiger Reserve poachers to protectors
  ["YES","conservation_action","anti_poaching_reform","","","","","Periyar Tiger Reserve","9.4667","77.15","protected_area","YES","","0","0","0","low","","Famous VSS model at Periyar - ex-poachers converted to forest protectors. v1 location correct."],
  # 56 Man sits face-to-face lion Delhi Zoo
  ["YES","hwc","zoo_enclosure_breach","African Lion","Panthera leo","VU","1","Delhi","28.7041","77.1025","city","YES","","0","1","0","high","","Man fell into lion enclosure at Delhi Zoo, rescued. Captive animal incident. VALIDATE: Include zoo incidents?"],
  # 57 Elusive tiger killed 2 seen camera Bandipur
  ["YES","hwc","tiger_attack","Tiger","Panthera tigris","EN","1","Bandipur Tiger Reserve","11.6667","76.6333","protected_area","NO","too_broad","2","0","0","critical","","Tiger that killed 2 people seen on camera trap at Bandipur. v1 pinned to Karnataka state centroid. 2 human fatalities."],
  # 58 Who killed the wandering rhino Assam Wire
  ["YES","mortality","suspected_poaching","Indian One-horned Rhinoceros","Rhinoceros unicornis","VU","1","Assam","26.2006","92.9376","state","YES","","0","0","1","critical","","Wandering rhino found dead in Assam. Investigation into cause. v1 state level appropriate."],
  # 59 Northeast few tigers outside protected areas
  ["YES","research","distribution_survey","Tiger","Panthera tigris","EN","","Northeast India","25.2744","92.9376","region","YES","","0","0","0","high","","Tiger distribution largely confined to PAs in Northeast India. Conservation concern. Region level correct."],
  # 60 Kerala to Cannes roar trip save the tiger
  ["YES","conservation_action","awareness_campaign","Tiger","Panthera tigris","EN","","Kerala","10.8505","76.2711","state","YES","","0","0","0","low","","International tiger conservation campaign starting in Kerala, traversing 25 countries. Origin location correct."],
  # 61 Braving monsoon save rhinos poaching Assam
  ["YES","conservation_action","anti_poaching_patrol","Indian One-horned Rhinoceros","Rhinoceros unicornis","VU","","Kaziranga National Park","26.5775","93.1711","protected_area","NO","too_broad","0","0","0","medium","","Anti-poaching patrols during monsoon in Assam (likely Kaziranga). v1 pinned to Assam state. VALIDATE: Specific PA?"],
  # 62 Karnataka sixth tiger reserve dacoits
  ["YES","policy","PA_designation","Tiger","Panthera tigris","EN","","Karnataka","15.3173","75.7139","state","NO","too_broad","0","0","0","medium","","Karnataka 6th tiger reserve establishment. v1 state centroid. VALIDATE: Which reserve? Likely Biligiri Rangaswamy / MM Hills area."],
  # 63 Rhinos Kaziranga floods politics Assam Wire
  ["YES","research","political_ecology","Indian One-horned Rhinoceros","Rhinoceros unicornis","VU","","Brahmaputra, Assam","26.8","93.7","region","YES","","0","0","0","medium","","Long-form on Kaziranga, Brahmaputra floods, rhino conservation and political dimensions."],
  # 64 239 rhinos killed Assam since 2001
  ["YES","research","historical_poaching_statistics","Indian One-horned Rhinoceros","Rhinoceros unicornis","VU","239","Assam","26.2006","92.9376","state","YES","","0","0","239","critical","","Historical aggregate: 239 rhinos poached in Assam 2001-2016, most at Kaziranga. Critical baseline."],
  # 65 Snow leopard skin recovered Uttarakhand
  ["YES","poaching","seizure","Snow Leopard","Panthera uncia","VU","1","Uttarakhand","30.0668","79.0193","state","YES","","0","0","1","critical","","Snow leopard skin recovered in Uttarakhand - implies poaching. State level correct."],
  # 66 Great Himalayan NP UNESCO heritage list
  ["YES","policy","UNESCO_heritage_nomination","","","","","Great Himalayan National Park","31.75","77.5833","protected_area","YES","","0","0","0","low","","GHNP on UNESCO WH tentative list (2009). Note: GHNP inscribed as full WHS in 2014. v1 location correct."],
]

new_rows = []
for i, (article, ann) in enumerate(zip(new_articles, annotations)):
    row = {
        'event_id': f"GS{115+i:03d}",
        'headline': article['headline'],
        'url': article['url'],
        'source': article['source'],
        'published': article['published'],
        'v1_place_name': article['place_name'],
        'v1_lat': article['lat'],
        'v1_lon': article['lon'],
        'valid_wildlife_article': ann[0],
        'event_type': ann[1],
        'event_subtype': ann[2],
        'species_common': ann[3],
        'species_scientific': ann[4],
        'species_iucn': ann[5],
        'animal_count': ann[6],
        'correct_place_name': ann[7],
        'correct_lat': ann[8],
        'correct_lon': ann[9],
        'location_precision': ann[10],
        'location_correct': ann[11],
        'location_error_type': ann[12],
        'human_casualties': ann[13],
        'human_injuries': ann[14],
        'animal_casualties': ann[15],
        'severity': ann[16],
        'cluster_id': ann[17],
        'notes_for_nikunj': ann[18],
    }
    new_rows.append(row)

with open('v2/data/gold_standard_annotations.csv', 'a', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writerows(new_rows)

print(f"Appended {len(new_rows)} rows (GS115-GS{114+len(new_rows)})")
print(f"Total rows now: {114 + len(new_rows)}")
