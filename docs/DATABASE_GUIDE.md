# Database guide — 0.6.0

The seed contains **57 distinct botanical oils (46 essential and 11 fixed)**, **164 distinct ready InChIKeys**, 186 ready compound-name records, 819 normalized name records, 68 botanical taxa, 119 analytical profiles and 2109 source observations. The 633 remaining names need review. Repeated profiles, source peaks and aliases do not inflate the home-page counters.

Three reviewed literature packs retain 90 analytical profiles and 1448 observations from 37 primary PMC papers. The original 661 composition records survive unchanged. Original table rows, values, units, uncertainty, source names, PMCID/DOI, table/row IDs, sample origin and cached-file SHA-256 remain traceable. Import hashes make repeat imports idempotent; incompatible changed manifests require reviewed migration. A SQLite backup is created before merging a new bundled literature pack into an existing user library.

The supplied combined CSV is integrated with a source-audit table: 434 corroborating duplicates, 85 source differences retained for review and 64 additional source values. Raw Word rows remain intact. No missing values become zero; unknown peaks, class totals, retention indices and oil yield are not compounds. Partial major-component tables remain labeled partial; percentages are not normalized to 100%.

Peppermint's published methyl acetate at RI1295 is retained but source-specific docking eligibility is false pending review; it is not silently changed to menthyl acetate. Its rounded individual rows sum to 99.52% although the printed total says 99.51%. Cumin is a market sample, peppermint a Moroccan reference, and selected grape, hibiscus and olive growing origins are unverified. Jasmine headspace is not extracted essential oil; olive fatty-acid pools are not native free-fatty-acid or triglyceride molecular compositions. Nymphaea alba is supported; the contradictory blue-lily article and unavailable olive annotation table were excluded.


The preparation filter distinguishes Essential Oils, Fixed Oils, Botanical Extracts, Resins and Aromatic Preparations and Individual Natural Compounds. The Ancient Egyptian Botanical Heritage view evaluates 12 candidates with evidence type, period, confidence, source and taxonomic scope. Genus-level biomarkers do not establish a modern species; reconstructed recipes and uncertain ancient plant names are identified as interpretations. Modern analytical chemistry is stored separately from historical associations.

Fixed-oil fatty-acid pools do not establish native free-acid abundance. Unresolved Moringa sum lipids, analytical TMS derivatives, silicone contaminants and source-suspect assignments are blocked. Structures beyond 900 Da, 80 heavy atoms or 25 rotatable bonds require specialist review. Candidate files, original observations and existing raw results survive these eligibility changes.

## Six-oil review

| Candidate | Decision and actual origin | Primary analytical source |
| --- | --- | --- |
| Sweet Marjoram | Added; Origanum majorana, Giza Egypt; full supplementary DOCX GC table | [PMC9563047](https://pmc.ncbi.nlm.nih.gov/articles/PMC9563047/) |
| Thyme | Already present; Thymus vulgaris, Egyptian sample; not duplicated | [PMC9605189](https://pmc.ncbi.nlm.nih.gov/articles/PMC9605189/) |
| Peppermint | Added; Mentha × piperita, Taounate Morocco reference; not Egyptian | [PMC5527698](https://pmc.ncbi.nlm.nih.gov/articles/PMC5527698/) |
| Sweet Basil | Added; Ocimum basilicum, Tanta Egypt | [PMC9578474](https://pmc.ncbi.nlm.nih.gov/articles/PMC9578474/) |
| Fennel | Added; Foeniculum vulgare, experimental cultivation control; exact field coordinates unreported | [PMC11866597](https://pmc.ncbi.nlm.nih.gov/articles/PMC11866597/) |
| Cumin | Added; Cuminum cyminum, Egyptian market; growing origin unverified | [PMC9570728](https://pmc.ncbi.nlm.nih.gov/articles/PMC9570728/) |
| Anise | Pimpinella anisum; Essential Oils; Agricultural Research Center, Cairo, Egypt | [PMC9023561](https://pmc.ncbi.nlm.nih.gov/articles/PMC9023561/) |
| Coriander | Coriandrum sativum; Essential Oils; Agricultural Research Center, Cairo, Egypt | [PMC9023561](https://pmc.ncbi.nlm.nih.gov/articles/PMC9023561/) |
| German Chamomile | Matricaria chamomilla; Essential Oils; Heliopolis University experimental field, Egypt | [PMC13315271](https://pmc.ncbi.nlm.nih.gov/articles/PMC13315271/) |
| Garlic | Allium sativum; Essential Oils; Arequipa, Peru | [PMC8615010](https://pmc.ncbi.nlm.nih.gov/articles/PMC8615010/) |
| Oregano | Origanum vulgare; Essential Oils; Mepaco medicinal farm, Egypt | [PMC6435767](https://pmc.ncbi.nlm.nih.gov/articles/PMC6435767/) |
| Damask Rose | Rosa × damascena; Essential Oils; Doalinn, Türkiye; cultivation origin unverified | [PMC10537268](https://pmc.ncbi.nlm.nih.gov/articles/PMC10537268/) |
| Camphor / Ravintsara | Cinnamomum camphora; Essential Oils; Pranarom, Belgium; cultivation origin unverified | [PMC9936101](https://pmc.ncbi.nlm.nih.gov/articles/PMC9936101/) |
| Cardamom | Elettaria cardamomum; Essential Oils; Pranarom, Belgium; cultivation origin unverified | [PMC9936101](https://pmc.ncbi.nlm.nih.gov/articles/PMC9936101/) |
| Tea | Camellia sinensis; Botanical Extracts; NIST reference material; cultivation origin unverified | [PMC4115333](https://pmc.ncbi.nlm.nih.gov/articles/PMC4115333/) |
| Coffee | Coffea arabica; Botanical Extracts; Royal Project Foundation, Chiang Mai, Thailand; commercial instant samples separately identified | [PMC7792775](https://pmc.ncbi.nlm.nih.gov/articles/PMC7792775/) |
| Coffee | Coffea arabica; Botanical Extracts; Royal Project Foundation, Chiang Mai, Thailand; commercial instant samples separately identified | [PMC7792775](https://pmc.ncbi.nlm.nih.gov/articles/PMC7792775/) |
| Coffee | Coffea arabica; Botanical Extracts; Royal Project Foundation, Chiang Mai, Thailand; commercial instant samples separately identified | [PMC7792775](https://pmc.ncbi.nlm.nih.gov/articles/PMC7792775/) |
| Coffee | Coffea arabica; Botanical Extracts; Commercial instant coffee, Thailand study; cultivation origin unverified | [PMC7792775](https://pmc.ncbi.nlm.nih.gov/articles/PMC7792775/) |
| Coffee | Coffea arabica; Botanical Extracts; Commercial instant coffee, Thailand study; cultivation origin unverified | [PMC7792775](https://pmc.ncbi.nlm.nih.gov/articles/PMC7792775/) |
| Sweet Almond | Prunus dulcis; Fixed Oils; Torre de Moncorvo, Portugal, 2019 | [PMC7700282](https://pmc.ncbi.nlm.nih.gov/articles/PMC7700282/) |
| Pistachio | Pistacia vera; Fixed Oils; Jafariyeh, Qom, Iran, 2022–2023 | [PMC11740597](https://pmc.ncbi.nlm.nih.gov/articles/PMC11740597/) |
| Sesame | Sesamum indicum; Fixed Oils; Poland (n = 3); commercial country of origin, not necessarily growing locality | [PMC4110403](https://pmc.ncbi.nlm.nih.gov/articles/PMC4110403/) |
| Safflower | Carthamus tinctorius; Fixed Oils; Poland (n = 3) France (n = 2); commercial country of origin, not necessarily growing locality | [PMC4110403](https://pmc.ncbi.nlm.nih.gov/articles/PMC4110403/) |
| Flax | Linum usitatissimum; Fixed Oils; Poland (n = 3) Italy (n = 1); commercial country of origin, not necessarily growing locality | [PMC4110403](https://pmc.ncbi.nlm.nih.gov/articles/PMC4110403/) |
| Castor | Ricinus communis; Fixed Oils; Nigeria study; exact growing locality not verified | [PMC10220419](https://pmc.ncbi.nlm.nih.gov/articles/PMC10220419/) |
| Pomegranate | Punica granatum; Botanical Extracts; Ibn-AlNafess herbalist, Beirut, Lebanon; cultivation origin unverified | [PMC4058451](https://pmc.ncbi.nlm.nih.gov/articles/PMC4058451/) |
| Myrrh | Commiphora myrrha; Essential Oils; Commercial drug material in China study; cultivation origin unverified | [PMC3796379](https://pmc.ncbi.nlm.nih.gov/articles/PMC3796379/) |
| Frankincense | Boswellia carterii; Essential Oils; Harraz Co., Cairo, Egypt; growing origin unverified | [PMC12030047](https://pmc.ncbi.nlm.nih.gov/articles/PMC12030047/) |
| Mastic | Pistacia lentiscus; Essential Oils; Cesme–Uzunkoy village, Izmir, Turkey, September 2016 | [PMC7248992](https://pmc.ncbi.nlm.nih.gov/articles/PMC7248992/) |
| Juniper | Juniperus phoenicea; Essential Oils; Boukornine mountain, Ben Arous, Tunisia, May 2022 | [PMC10673065](https://pmc.ncbi.nlm.nih.gov/articles/PMC10673065/) |
| Juniper | Juniperus phoenicea; Essential Oils; Boukornine mountain, Ben Arous, Tunisia, May 2022 | [PMC10673065](https://pmc.ncbi.nlm.nih.gov/articles/PMC10673065/) |
| Cedar | Cedrus atlantica; Resins and Aromatic Preparations; Les Arômes de Ben Sim, Azrou, Morocco, October 2009 | [PMC13144440](https://pmc.ncbi.nlm.nih.gov/articles/PMC13144440/) |
| Moringa peregrina | Moringa peregrina; Fixed Oils; Al Dhakhlia, Oman, June 2017 | [PMC6571088](https://pmc.ncbi.nlm.nih.gov/articles/PMC6571088/) |
| Moringa oleifera | Moringa oleifera; Fixed Oils; Limpopo, South Africa, September 2017 | [PMC6571088](https://pmc.ncbi.nlm.nih.gov/articles/PMC6571088/) |
| Desert Date | Balanites aegyptiaca; Fixed Oils; Tata, Morocco, 2020 | [PMC11011647](https://pmc.ncbi.nlm.nih.gov/articles/PMC11011647/) |
| Desert Date | Balanites aegyptiaca; Botanical Extracts; Wadi El Gemal National Park, Marsa Alam, Egypt, January 2022 | [PMC10359763](https://pmc.ncbi.nlm.nih.gov/articles/PMC10359763/) |

## Primary sources

- [PMC6044011: Effective antioxidant, antimicrobial and anticancer activities of essential oils of horticultural aromatic crops in northern Egypt](https://pmc.ncbi.nlm.nih.gov/articles/PMC6044011/) — DOI 10.1186/s12906-018-2262-1
- [PMC9605189: GC–MS Profiling of Naturally Extracted Essential Oils: Antimicrobial and Beverage Preservative Actions](https://pmc.ncbi.nlm.nih.gov/articles/PMC9605189/) — DOI 10.3390/life12101587
- [PMC8398089: Metabolomic Profiles of Essential Oils from Selected Rosa Varieties and Their Antimicrobial Activities](https://pmc.ncbi.nlm.nih.gov/articles/PMC8398089/) — DOI 10.3390/plants10081721
- [PMC12988214: Comparative analysis of flower volatiles from four Jasminum species growing in Egypt using multivariate analysis](https://pmc.ncbi.nlm.nih.gov/articles/PMC12988214/) — DOI 10.1038/s41598-026-39688-w
- [PMC13338266: Volatile composition of essential oils from major Egyptian Citrus cultivars: a multivariate chemometric approach](https://pmc.ncbi.nlm.nih.gov/articles/PMC13338266/) — DOI 10.1038/s41598-026-60409-w
- [PMC9767472: Antiviral activity of Lavandula angustifolia L. and Salvia officinalis L. essential oils against avian influenza H5N1 virus](https://pmc.ncbi.nlm.nih.gov/articles/PMC9767472/) — DOI 10.1016/j.jafr.2021.100135
- [PMC5240310: Profile of bioactive compounds in Nymphaea alba L. leaves growing in Egypt: hepatoprotective, antioxidant and anti-inflammatory activity](https://pmc.ncbi.nlm.nih.gov/articles/PMC5240310/) — DOI 10.1186/s12906-017-1561-2
- [PMC12957211: He–Ne laser irradiation enhances curcuminoid content in Curcuma longa: a green strategy for functional antioxidants and antimicrobial ingredients](https://pmc.ncbi.nlm.nih.gov/articles/PMC12957211/) — DOI 10.3389/fnut.2026.1758942
- [PMC11325491: Mitigating Acetaminophen-Induced Kidney Injury: The Protective Role of Grape Seed and Peanut Skin Extracts through the iNOS/CYP2E1 Pathway](https://pmc.ncbi.nlm.nih.gov/articles/PMC11325491/) — DOI 10.1021/acsomega.4c05534
- [PMC10788201: A pharmacological and toxicological biochemical study of cardiovascular regulatory effects of hibiscus, corn silk, marjoram, and chamomile](https://pmc.ncbi.nlm.nih.gov/articles/PMC10788201/) — DOI 10.1016/j.heliyon.2023.e22659
- [PMC11607071: In sight on olive oil maceration and supercritical CO2 in extracting rosemary essential oil](https://pmc.ncbi.nlm.nih.gov/articles/PMC11607071/) — DOI 10.1038/s41598-024-79832-y
- [PMC9563047: Origanum majorana essential oil improves the rat’s sexual behavior and testicular oxidative damage induced by imidacloprid via modulating the steroidogenesis pathways](https://pmc.ncbi.nlm.nih.gov/articles/PMC9563047/) — DOI 10.1016/j.jsps.2022.06.016
- [PMC9578474: In vitro and in silico β-lactamase inhibitory properties and phytochemical profile of Ocimum basilicum cultivated in central delta of Egypt](https://pmc.ncbi.nlm.nih.gov/articles/PMC9578474/) — DOI 10.1080/13880209.2022.2127791
- [PMC11666597: Influence of ethephon and soil treatments on the essential oil composition of sweet fennel and its biological activities](https://pmc.ncbi.nlm.nih.gov/articles/PMC11666597/) — DOI 10.1038/s41598-024-82204-1
- [PMC9570728: GC-MS Profiling, Anti-Helicobacter pylori, and Anti-Inflammatory Activities of Three Apiaceous Fruits’ Essential Oils](https://pmc.ncbi.nlm.nih.gov/articles/PMC9570728/) — DOI 10.3390/plants11192617
- [PMC5527698: African peppermint (Mentha piperita) from Morocco: Chemical composition and antimicrobial properties of essential oil](https://pmc.ncbi.nlm.nih.gov/articles/PMC5527698/) — DOI 10.4103/japtr.JAPTR_11_17
- [PMC9023561: Coriander (Coriandrum sativum L.) essential oil and oil-loaded nano-formulations as an anti-aging potentiality via TGFβ/SMAD pathway](https://pmc.ncbi.nlm.nih.gov/articles/PMC9023561/) — DOI 10.1038/s41598-022-10494-4
- [PMC13315271: Shifts in the Rhizosphere Bacterial Community and Improved Essential Oil Yield and Quality in Chamomilla recutita L. Plant Through Cyanobacterial Inoculation](https://pmc.ncbi.nlm.nih.gov/articles/PMC13315271/) — DOI 10.1007/s00248-026-02815-1
- [PMC8615010: Chemical Constituents, In Vitro Antioxidant Activity and In Silico Study on NADPH Oxidase of Allium sativum L. (Garlic) Essential Oil](https://pmc.ncbi.nlm.nih.gov/articles/PMC8615010/) — DOI 10.3390/antiox10111844
- [PMC6435767: Chemical profiling, biostatic and biocidal dynamics of Origanum vulgare L. essential oil](https://pmc.ncbi.nlm.nih.gov/articles/PMC6435767/) — DOI 10.1186/s13568-019-0764-y
- [PMC10537268: Comparative In Vitro and In Silico Enzyme Inhibitory Screening of Rosa x damascena and Pelargonium graveolens Essential Oils and Geraniol](https://pmc.ncbi.nlm.nih.gov/articles/PMC10537268/) — DOI 10.3390/plants12183296
- [PMC9936101: Essential oil of Cymbopogon martini, source of geraniol, as a potential antibacterial agent against Bacillus subtilis, a pathogen of the bakery industry](https://pmc.ncbi.nlm.nih.gov/articles/PMC9936101/) — DOI 10.12688/f1000research.54196.2
- [PMC4115333: Determination of Catechins and Caffeine in Camillia sinensis Raw Materials, Extracts, and Dietary Supplements by HPLC-UV: Single-Laboratory Validation](https://pmc.ncbi.nlm.nih.gov/articles/PMC4115333/) — DOI 10.5740/jaoacint.10-488
- [PMC7792775: Anti-Platelet Aggregation and Anti-Cyclooxygenase Activities for a Range of Coffee Extracts (Coffea arabica)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7792775/) — DOI 10.3390/molecules26010010
- [PMC7700282: Effects of Different Processing Treatments on Almond (Prunus dulcis) Bioactive Compounds, Antioxidant Activities, Fatty Acids, and Sensorial Characteristics](https://pmc.ncbi.nlm.nih.gov/articles/PMC7700282/) — DOI 10.3390/plants9111627
- [PMC11740597: Agronomic characteristics, mineral nutrient content, antioxidant capacity, biochemical composition, and fatty acid profile of Iranian pistachio (Pistacia vera L.) cultivars](https://pmc.ncbi.nlm.nih.gov/articles/PMC11740597/) — DOI 10.1186/s12870-025-06094-9
- [PMC4110403: The Antioxidant Activity and Oxidative Stability of Cold-Pressed Oils](https://pmc.ncbi.nlm.nih.gov/articles/PMC4110403/) — DOI 10.1007/s11746-014-2479-1
- [PMC10220419: Experimental and theoretical assessment of phenomena linked with separation and purification of biodiesel from Ricinus communis seed oil](https://pmc.ncbi.nlm.nih.gov/articles/PMC10220419/) — DOI 10.1016/j.heliyon.2023.e16536
- [PMC4058451: Amelioration of Diabetes and Painful Diabetic Neuropathy by Punica granatum L. Extract and Its Spray Dried Biopolymeric Dispersions](https://pmc.ncbi.nlm.nih.gov/articles/PMC4058451/) — DOI 10.1155/2014/180495
- [PMC3796379: Composition and potential anticancer activities of essential oils obtained from myrrh and frankincense](https://pmc.ncbi.nlm.nih.gov/articles/PMC3796379/) — DOI 10.3892/ol.2013.1520
- [PMC12030047: Anti-Tumor Potential of Frankincense Essential Oil and Its Nano-Formulation in Breast Cancer: An In Vivo and In Vitro Study](https://pmc.ncbi.nlm.nih.gov/articles/PMC12030047/) — DOI 10.3390/pharmaceutics17040426
- [PMC7248992: Chemical Characterization and Biological Activity of the Mastic Gum Essential Oils of Pistacia lentiscus var. chia from Turkey †](https://pmc.ncbi.nlm.nih.gov/articles/PMC7248992/) — DOI 10.3390/molecules25092136
- [PMC10673065: Insights on Juniperus phoenicea Essential Oil as Potential Anti-Proliferative, Anti-Tyrosinase, and Antioxidant Candidate](https://pmc.ncbi.nlm.nih.gov/articles/PMC10673065/) — DOI 10.3390/molecules28227547
- [PMC13144440: An archaeo-metabolomics approach for identifying cedar tar in archaeological samples: differentiating plant products and production processes](https://pmc.ncbi.nlm.nih.gov/articles/PMC13144440/) — DOI 10.1038/s41598-026-50080-6
- [PMC6571088: Ultrahigh-pressure supercritical fluid extraction and chromatography of Moringa oleifera and Moringa peregrina seed lipids](https://pmc.ncbi.nlm.nih.gov/articles/PMC6571088/) — DOI 10.1007/s00216-019-01850-x
- [PMC11011647: Chemical Composition and Geographic Variation of Cold Pressed Balanites aegyptiaca Kernel Oil](https://pmc.ncbi.nlm.nih.gov/articles/PMC11011647/) — DOI 10.3390/foods13071135
- [PMC10359763: Comparison of Balanites aegyptiaca parts: metabolome providing insights into plant health benefits and valorization purposes as analyzed using multiplex GC-MS, LC-MS, NMR-based metabolomics, and molecular networking†](https://pmc.ncbi.nlm.nih.gov/articles/PMC10359763/) — DOI 10.1039/d3ra03141a

The external Literature_Catalog_EN.csv and Literature_Observations_EN.csv describe the three reviewed literature packs. Full seed records remain available in SQLite.
