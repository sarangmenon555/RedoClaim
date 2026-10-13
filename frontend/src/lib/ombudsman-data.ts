export interface OmbudsmanOffice {
  center: string;
  statesCovered: string[];
  address: string;
  email: string;
  phone?: string;
  districts?: string[];
}

// Source: Council for Insurance Ombudsman (CIOI) published jurisdiction
// list. Filing at the wrong center is a real, avoidable rejection reason —
// this is static reference data, no LLM call. Verify against
// cioins.co.in before filing, since jurisdictions are occasionally revised.
export const OMBUDSMAN_OFFICES: OmbudsmanOffice[] = [
  {
    center: "Ahmedabad",
    statesCovered: ["Gujarat", "Dadra and Nagar Haveli and Daman and Diu"],
    address: "Jeevan Prakash Building, 6th Floor, Tilak Marg, Relief Road, Ahmedabad – 380001",
    email: "oio.ahmedabad@cioins.co.in",
    phone: "079 - 25501201 / 02",
  },
  {
    center: "Bengaluru",
    statesCovered: ["Karnataka"],
    address: "Jeevan Soudha Building, PID No. 57-27-N-19, Ground Floor, 19/19, 24th Main Road, JP Nagar, 1st Phase, Bengaluru – 560078",
    email: "oio.bengaluru@cioins.co.in",
    phone: "080 - 26652048 / 26652049",
  },
  {
    center: "Bhopal",
    statesCovered: ["Madhya Pradesh", "Chhattisgarh"],
    address: "1st Floor, Jeevan Shikha, 60-B, Hoshangabad Road, Opp. Gayatri Mandir, Arera Hills, Bhopal – 462011",
    email: "oio.bhopal@cioins.co.in",
    phone: "0755 - 2769201 / 2769202 / 2769203",
  },
  {
    center: "Bhubaneswar",
    statesCovered: ["Odisha"],
    address: "62, Forest Park, Bhubaneswar – 751009",
    email: "oio.bhubaneswar@cioins.co.in",
    phone: "0674 - 2596461 / 2596455 / 2596429 / 2596003",
  },
  {
    center: "Chandigarh",
    statesCovered: ["Punjab", "Haryana (excluding Gurugram, Faridabad, Sonepat and Bahadurgarh)", "Himachal Pradesh", "Jammu and Kashmir", "Ladakh", "Chandigarh"],
    address: "Jeevan Deep Building, SCO 20-27, Ground Floor, Sector 17-A, Chandigarh – 160017",
    email: "oio.chandigarh@cioins.co.in",
    phone: "0172 - 2706468",
  },
  {
    center: "Chennai",
    statesCovered: ["Tamil Nadu", "Puducherry town and Karaikal"],
    address: "Fatima Akhtar Court, 4th Floor, 453, Anna Salai, Teynampet, Chennai – 600018",
    email: "oio.chennai@cioins.co.in",
    phone: "044 - 24333668 / 24333678",
  },
  {
    center: "Delhi",
    statesCovered: ["Delhi", "Haryana districts of Gurugram, Faridabad, Sonepat and Bahadurgarh"],
    address: "2/2 A, Universal Insurance Building, Asaf Ali Road, New Delhi – 110002",
    email: "oio.delhi@cioins.co.in",
    phone: "011 - 46013992 / 23213504 / 23232481",
  },
  {
    center: "Guwahati",
    statesCovered: ["Assam", "Meghalaya", "Manipur", "Mizoram", "Arunachal Pradesh", "Nagaland", "Tripura"],
    address: "Jeevan Nivesh, 5th Floor, Near Pan Bazar, S.S. Road, Guwahati – 781001",
    email: "oio.guwahati@cioins.co.in",
    phone: "0361 - 2632204 / 2602205 / 2631307",
  },
  {
    center: "Hyderabad",
    statesCovered: ["Andhra Pradesh", "Telangana", "Yanam (part of Puducherry)"],
    address: "6-2-46, 1st Floor, Moin Court, Lane Opp. Hyundai Showroom, A.C. Guards, Lakdi-Ka-Pool, Hyderabad – 500004",
    email: "oio.hyderabad@cioins.co.in",
    phone: "040 - 23312122 / 23376991 / 23376599 / 23328709 / 23325325",
  },
  {
    center: "Jaipur",
    statesCovered: ["Rajasthan"],
    address: "Jeevan Nidhi – II Bldg., Ground Floor, Bhawani Singh Marg, Jaipur – 302005",
    email: "oio.jaipur@cioins.co.in",
    phone: "0141 - 2740363",
  },
  {
    center: "Kochi",
    statesCovered: ["Keralam", "Lakshadweep", "Mahe (part of Puducherry)"],
    address: "10th Floor, Jeevan Prakash, LIC Building, Opp. Maharaja's College Ground, M.G. Road, Kochi – 682011",
    email: "oio.ernakulam@cioins.co.in",
    phone: "0484 - 2358759",
  },
  {
    center: "Kolkata",
    statesCovered: ["West Bengal", "Sikkim", "Andaman and Nicobar Islands"],
    address: "Hindustan Building Annexe, 7th Floor, 4, C.R. Avenue, Kolkata – 700072",
    email: "oio.kolkata@cioins.co.in",
    phone: "033 - 22124339 / 22124341",
  },
  {
    center: "Lucknow",
    statesCovered: ["Uttar Pradesh (listed districts, including Lucknow, Kanpur, Prayagraj, Varanasi, Ayodhya and Gorakhpur)"],
    address: "6th Floor, Jeevan Bhawan, Phase-II, Nawal Kishore Road, Hazratganj, Lucknow – 226001",
    email: "oio.lucknow@cioins.co.in",
    phone: "0522 - 4002082 / 3500613",
    districts: ["Lalitpur", "Jhansi", "Mahoba", "Hamirpur", "Banda", "Chitrakoot", "Prayagraj", "Mirzapur", "Sonbhadra", "Fatehpur", "Pratapgarh", "Jaunpur", "Varanasi", "Ghazipur", "Jalaun", "Kanpur", "Lucknow", "Unnao", "Sitapur", "Lakhimpur Kheri", "Bahraich", "Barabanki", "Raebareli", "Shravasti", "Gonda", "Ayodhya", "Amethi", "Kaushambi", "Balrampur", "Basti", "Ambedkar Nagar", "Sultanpur", "Maharajganj", "Sant Kabir Nagar", "Azamgarh", "Kushinagar", "Gorakhpur", "Deoria", "Mau", "Chandauli", "Ballia", "Siddharthnagar"],
  },
  {
    center: "Mumbai",
    statesCovered: ["Mumbai Metropolitan Region, excluding the Mumbai wards M/East, M/West, N, S and T and the Navi Mumbai area, which the Thane office covers"],
    address: "3rd Floor, Jeevan Seva Annexe, S.V. Road, Santacruz (West), Mumbai – 400054",
    email: "oio.mumbai@cioins.co.in",
    phone: "022 - 69038800 / 27 / 29 / 31 / 32 / 33",
  },
  {
    center: "Noida",
    statesCovered: ["Uttarakhand", "Uttar Pradesh (listed districts, including Noida, Ghaziabad, Meerut, Agra, Bareilly and Moradabad)"],
    address: "Bhagwan Sahai Palace, 4th Floor, Main Road, Naya Bans, Sector 15, Distt: Gautam Buddh Nagar, U.P. – Noida – 201301",
    email: "oio.noida@cioins.co.in",
    phone: "0120 - 2514252 / 2514253",
    districts: ["Agra", "Aligarh", "Baghpat", "Bareilly", "Bijnor", "Badaun", "Bulandshahr", "Etah", "Kannauj", "Mainpuri", "Mathura", "Meerut", "Moradabad", "Muzaffarnagar", "Auraiya", "Pilibhit", "Etawah", "Farrukhabad", "Firozabad", "Gautam Buddh Nagar", "Ghaziabad", "Hardoi", "Shahjahanpur", "Hapur", "Shamli", "Rampur", "Kasganj", "Sambhal", "Amroha", "Hathras", "Saharanpur"],
  },
  {
    center: "Patna",
    statesCovered: ["Bihar", "Jharkhand"],
    address: "2nd Floor, Lalit Bhawan, Bailey Road, Patna – 800001",
    email: "oio.patna@cioins.co.in",
    phone: "0612 - 2547068",
  },
  {
    center: "Pune",
    statesCovered: ["Goa", "Maharashtra (excluding Navi Mumbai, Thane, Palghar and Raigad districts and the Mumbai Metropolitan Region)"],
    address: "Jeevan Darshan Bldg., 3rd Floor, C.T.S. No.s. 195 to 198, N.C. Kelkar Road, Narayan Peth, Pune – 411030",
    email: "oio.pune@cioins.co.in",
    phone: "020 - 24471175",
  },
  {
    center: "Thane",
    statesCovered: ["Navi Mumbai", "Thane district", "Raigad district", "Palghar district", "Mumbai wards M/East, M/West, N, S and T"],
    address: "Jeevan Chintamani Building, 2nd Floor, Near New RTO Office, Louis Wadi, Vasantrao Naik Mahamarg, Thane (West) – 400604",
    email: "oio.thane@cioins.co.in",
    phone: "022 - 20812868 / 69",
  },
];

// City -> Ombudsman center mapping for common major cities, so users can
// search by city name rather than needing to know their center already.
export const CITY_TO_CENTER: Record<string, string> = {
  "ahmedabad": "Ahmedabad", "surat": "Ahmedabad", "vadodara": "Ahmedabad", "rajkot": "Ahmedabad",
  "bengaluru": "Bengaluru", "bangalore": "Bengaluru", "mysuru": "Bengaluru", "mysore": "Bengaluru",
  "bhopal": "Bhopal", "indore": "Bhopal", "raipur": "Bhopal", "jabalpur": "Bhopal",
  "bhubaneswar": "Bhubaneswar", "cuttack": "Bhubaneswar",
  "chandigarh": "Chandigarh", "ludhiana": "Chandigarh", "amritsar": "Chandigarh", "shimla": "Chandigarh", "jammu": "Chandigarh", "srinagar": "Chandigarh",
  "chennai": "Chennai", "coimbatore": "Chennai", "madurai": "Chennai", "puducherry": "Chennai",
  "delhi": "Delhi", "new delhi": "Delhi", "gurugram": "Delhi", "gurgaon": "Delhi", "faridabad": "Delhi", "sonipat": "Delhi", "sonepat": "Delhi", "bahadurgarh": "Delhi",
  "guwahati": "Guwahati", "shillong": "Guwahati", "imphal": "Guwahati", "agartala": "Guwahati",
  "hyderabad": "Hyderabad", "secunderabad": "Hyderabad", "visakhapatnam": "Hyderabad", "vijayawada": "Hyderabad", "warangal": "Hyderabad",
  "jaipur": "Jaipur", "jodhpur": "Jaipur", "udaipur": "Jaipur", "kota": "Jaipur",
  "kochi": "Kochi", "ernakulam": "Kochi", "thiruvananthapuram": "Kochi", "kozhikode": "Kochi", "kollam": "Kochi",
  "kolkata": "Kolkata", "siliguri": "Kolkata", "gangtok": "Kolkata", "port blair": "Kolkata", "sri vijaya puram": "Kolkata",
  "lucknow": "Lucknow", "kanpur": "Lucknow", "varanasi": "Lucknow", "prayagraj": "Lucknow", "allahabad": "Lucknow", "ayodhya": "Lucknow", "faizabad": "Lucknow", "gorakhpur": "Lucknow",
  "mumbai": "Mumbai",
  "thane": "Thane", "navi mumbai": "Thane", "kalyan": "Thane", "dombivli": "Thane", "bhiwandi": "Thane", "vasai": "Thane", "virar": "Thane", "palghar": "Thane", "panvel": "Thane", "raigad": "Thane",
  "noida": "Noida", "ghaziabad": "Noida", "agra": "Noida", "meerut": "Noida", "dehradun": "Noida", "haridwar": "Noida",
  "patna": "Patna", "ranchi": "Patna", "jamshedpur": "Patna", "gaya": "Patna",
  "pune": "Pune", "nagpur": "Pune", "nashik": "Pune", "aurangabad": "Pune", "chhatrapati sambhajinagar": "Pune", "sambhajinagar": "Pune", "ahilyanagar": "Pune", "ahmednagar": "Pune", "kolhapur": "Pune", "solapur": "Pune", "goa": "Pune", "panaji": "Pune",
};

export interface StateOrUT {
  name: string;
  type: "State" | "Union Territory";
  centers: string[];
  note?: string;
}

export const STATES_AND_UTS: StateOrUT[] = [
  { name: "Andhra Pradesh", type: "State", centers: ["Hyderabad"] },
  { name: "Arunachal Pradesh", type: "State", centers: ["Guwahati"] },
  { name: "Assam", type: "State", centers: ["Guwahati"] },
  { name: "Bihar", type: "State", centers: ["Patna"] },
  { name: "Chhattisgarh", type: "State", centers: ["Bhopal"] },
  { name: "Goa", type: "State", centers: ["Pune"] },
  { name: "Gujarat", type: "State", centers: ["Ahmedabad"] },
  {
    name: "Haryana",
    type: "State",
    centers: ["Chandigarh", "Delhi"],
    note: "The districts of Gurugram, Faridabad, Sonepat and Bahadurgarh are served by the Delhi office. The rest of Haryana is served by the Chandigarh office.",
  },
  { name: "Himachal Pradesh", type: "State", centers: ["Chandigarh"] },
  { name: "Jharkhand", type: "State", centers: ["Patna"] },
  { name: "Karnataka", type: "State", centers: ["Bengaluru"] },
  { name: "Keralam", type: "State", centers: ["Kochi"] },
  { name: "Madhya Pradesh", type: "State", centers: ["Bhopal"] },
  {
    name: "Maharashtra",
    type: "State",
    centers: ["Mumbai", "Pune", "Thane"],
    note: "Maharashtra is divided between three offices. Thane covers Thane, Palghar and Raigad districts, Navi Mumbai and the Mumbai wards M/East, M/West, N, S and T. Mumbai covers the rest of the Mumbai Metropolitan Region. Pune covers the rest of the state. Your district or city decides the office.",
  },
  { name: "Manipur", type: "State", centers: ["Guwahati"] },
  { name: "Meghalaya", type: "State", centers: ["Guwahati"] },
  { name: "Mizoram", type: "State", centers: ["Guwahati"] },
  { name: "Nagaland", type: "State", centers: ["Guwahati"] },
  { name: "Odisha", type: "State", centers: ["Bhubaneswar"] },
  { name: "Punjab", type: "State", centers: ["Chandigarh"] },
  { name: "Rajasthan", type: "State", centers: ["Jaipur"] },
  { name: "Sikkim", type: "State", centers: ["Kolkata"] },
  { name: "Tamil Nadu", type: "State", centers: ["Chennai"] },
  { name: "Telangana", type: "State", centers: ["Hyderabad"] },
  { name: "Tripura", type: "State", centers: ["Guwahati"] },
  {
    name: "Uttar Pradesh",
    type: "State",
    centers: ["Lucknow", "Noida"],
    note: "Uttar Pradesh is divided between the Lucknow and Noida offices. Your district decides the office, so please check your district against the list on cioins.co.in.",
  },
  { name: "Uttarakhand", type: "State", centers: ["Noida"] },
  { name: "West Bengal", type: "State", centers: ["Kolkata"] },
  { name: "Andaman and Nicobar Islands", type: "Union Territory", centers: ["Kolkata"] },
  { name: "Chandigarh", type: "Union Territory", centers: ["Chandigarh"] },
  { name: "Dadra and Nagar Haveli and Daman and Diu", type: "Union Territory", centers: ["Ahmedabad"] },
  { name: "Delhi", type: "Union Territory", centers: ["Delhi"] },
  { name: "Jammu and Kashmir", type: "Union Territory", centers: ["Chandigarh"] },
  { name: "Ladakh", type: "Union Territory", centers: ["Chandigarh"] },
  { name: "Lakshadweep", type: "Union Territory", centers: ["Kochi"] },
  {
    name: "Puducherry",
    type: "Union Territory",
    centers: ["Chennai", "Kochi", "Hyderabad"],
    note: "Puducherry town and Karaikal fall under Chennai, Mahe under Kochi, and Yanam under Hyderabad.",
  },
];
