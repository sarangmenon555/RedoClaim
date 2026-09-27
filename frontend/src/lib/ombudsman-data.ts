export interface OmbudsmanOffice {
  center: string;
  statesCovered: string[];
  address: string;
  email: string;
  phone?: string;
}

// Source: Council for Insurance Ombudsman (CIOI) published jurisdiction
// list. Filing at the wrong center is a real, avoidable rejection reason —
// this is static reference data, no LLM call. Verify against
// cioins.co.in before filing, since jurisdictions are occasionally revised.
export const OMBUDSMAN_OFFICES: OmbudsmanOffice[] = [
  {
    center: "Ahmedabad",
    statesCovered: ["Gujarat", "Dadra & Nagar Haveli", "Daman & Diu"],
    address: "Jeevan Prakash Building, 6th Floor, Tilak Marg, Relief Road, Ahmedabad – 380001",
    email: "bimalokpal.ahmedabad@cioins.co.in",
  },
  {
    center: "Bengaluru",
    statesCovered: ["Karnataka"],
    address: "Jeevan Soudha Building, PID No. 57-27-N-19, Ground Floor, 19/19, 24th Main Road, JP Nagar, 1st Phase, Bengaluru – 560078",
    email: "bimalokpal.bengaluru@cioins.co.in",
  },
  {
    center: "Bhopal",
    statesCovered: ["Madhya Pradesh", "Chhattisgarh"],
    address: "Janak Vihar Complex, 2nd Floor, 6, Malviya Nagar, Opp. Airtel Office, Near New Market, Bhopal – 462003",
    email: "bimalokpal.bhopal@cioins.co.in",
  },
  {
    center: "Bhubaneswar",
    statesCovered: ["Odisha"],
    address: "62, Forest Park, Bhubaneswar – 751009",
    email: "bimalokpal.bhubaneswar@cioins.co.in",
  },
  {
    center: "Chandigarh",
    statesCovered: ["Punjab", "Haryana", "Himachal Pradesh", "Jammu & Kashmir", "Union Territory of Chandigarh"],
    address: "S.C.O. No. 101-103, 2nd Floor, Batra Building, Sector 17-D, Chandigarh – 160017",
    email: "bimalokpal.chandigarh@cioins.co.in",
  },
  {
    center: "Chennai",
    statesCovered: ["Tamil Nadu", "Puducherry (Union Territory)"],
    address: "Fatima Akhtar Court, 4th Floor, 453, Anna Salai, Teynampet, Chennai – 600018",
    email: "bimalokpal.chennai@cioins.co.in",
  },
  {
    center: "Delhi",
    statesCovered: ["Delhi", "parts of Rajasthan"],
    address: "2/2 A, Universal Insurance Building, Asaf Ali Road, New Delhi – 110002",
    email: "bimalokpal.delhi@cioins.co.in",
  },
  {
    center: "Guwahati",
    statesCovered: ["Assam", "Meghalaya", "Manipur", "Mizoram", "Arunachal Pradesh", "Nagaland", "Tripura"],
    address: "Jeevan Nivesh, 5th Floor, Nr. Panbazar Overbridge, S.S. Road, Guwahati – 781001",
    email: "bimalokpal.guwahati@cioins.co.in",
  },
  {
    center: "Hyderabad",
    statesCovered: ["Andhra Pradesh", "Telangana", "Yanam (Puducherry UT)"],
    address: "6-2-46, 1st Floor, Moin Court, Lane Opp. Saleem Function Palace, A.C. Guards, Lakdi-Ka-Pool, Hyderabad – 500004",
    email: "bimalokpal.hyderabad@cioins.co.in",
  },
  {
    center: "Jaipur",
    statesCovered: ["Rajasthan"],
    address: "Jeevan Nidhi – II Bldg., Ground Floor, Bhawani Singh Marg, Jaipur – 302005",
    email: "bimalokpal.jaipur@cioins.co.in",
  },
  {
    center: "Ernakulam",
    statesCovered: ["Kerala", "Lakshadweep", "Mahe (part of Puducherry UT)"],
    address: "2nd Floor, Pulinat Building, Opp. Cochin Shipyard, M.G. Road, Ernakulam – 682015",
    email: "bimalokpal.ernakulam@cioins.co.in",
  },
  {
    center: "Kolkata",
    statesCovered: ["West Bengal", "Sikkim", "Andaman & Nicobar Islands"],
    address: "Hindustan Building, Annexe, 4th Floor, 4, C.R. Avenue, Kolkata – 700072",
    email: "bimalokpal.kolkata@cioins.co.in",
  },
  {
    center: "Lucknow",
    statesCovered: ["Uttar Pradesh (districts near Lucknow)", "Uttarakhand"],
    address: "6th Floor, Jeevan Bhawan, Phase-II, Nawal Kishore Road, Hazratganj, Lucknow – 226001",
    email: "bimalokpal.lucknow@cioins.co.in",
  },
  {
    center: "Mumbai",
    statesCovered: ["Maharashtra (excluding Nagpur region)", "Goa"],
    address: "3rd Floor, Jeevan Seva Annexe, S.V. Road, Santacruz (West), Mumbai – 400054",
    email: "bimalokpal.mumbai@cioins.co.in",
  },
  {
    center: "Noida",
    statesCovered: ["Uttar Pradesh (remaining districts)"],
    address: "Bhagwan Sahai Palace, 4th Floor, Main Road, Naya Bans, Sector 15, Distt: Gautam Buddh Nagar, U.P. – Noida – 201301",
    email: "bimalokpal.noida@cioins.co.in",
  },
  {
    center: "Patna",
    statesCovered: ["Bihar", "Jharkhand"],
    address: "1st Floor, Kalpana Arcade Building, Bazar Samiti Road, Bahadurpur, Patna – 800006",
    email: "bimalokpal.patna@cioins.co.in",
  },
  {
    center: "Pune",
    statesCovered: ["Maharashtra (Nagpur region)"],
    address: "Jeevan Darshan Bldg., 3rd Floor, C.T.S. No.s. 195 to 198, N.C. Kelkar Road, Narayan Peth, Pune – 411030",
    email: "bimalokpal.pune@cioins.co.in",
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
  "delhi": "Delhi", "new delhi": "Delhi", "gurugram": "Delhi", "gurgaon": "Delhi", "faridabad": "Delhi",
  "guwahati": "Guwahati", "shillong": "Guwahati", "imphal": "Guwahati", "agartala": "Guwahati",
  "hyderabad": "Hyderabad", "secunderabad": "Hyderabad", "visakhapatnam": "Hyderabad", "vijayawada": "Hyderabad", "warangal": "Hyderabad",
  "jaipur": "Jaipur", "jodhpur": "Jaipur", "udaipur": "Jaipur", "kota": "Jaipur",
  "kochi": "Ernakulam", "ernakulam": "Ernakulam", "thiruvananthapuram": "Ernakulam", "kozhikode": "Ernakulam", "kollam": "Ernakulam",
  "kolkata": "Kolkata", "siliguri": "Kolkata", "gangtok": "Kolkata", "port blair": "Kolkata",
  "lucknow": "Lucknow", "kanpur": "Lucknow", "dehradun": "Lucknow", "haridwar": "Lucknow",
  "mumbai": "Mumbai", "thane": "Mumbai", "nashik": "Mumbai", "goa": "Mumbai", "panaji": "Mumbai",
  "noida": "Noida", "ghaziabad": "Noida", "agra": "Noida", "varanasi": "Noida", "prayagraj": "Noida", "allahabad": "Noida", "meerut": "Noida",
  "patna": "Patna", "ranchi": "Patna", "jamshedpur": "Patna", "gaya": "Patna",
  "pune": "Pune", "nagpur": "Pune", "aurangabad": "Pune",
};
