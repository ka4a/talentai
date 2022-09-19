import { defineMessage } from '@lingui/macro';

export const JOB_STATUS_CHOICES = [
  { value: 'open', name: defineMessage({ message: 'Open' }).id, color: 'primary' },
  { value: 'on_hold', name: defineMessage({ message: 'On Hold' }).id, color: 'dark' },
  {
    value: 'filled',
    name: defineMessage({ message: 'Filled' }).id,
    color: 'secondary',
  },
  { value: 'closed', name: defineMessage({ message: 'Closed' }).id, color: 'success' },
];

export const PROPOSAL_STATUS_GROUP_CATEGORY_CHOICES = [
  { value: 'new', name: defineMessage({ message: 'New' }).id },
  { value: 'proceeding', name: defineMessage({ message: 'Proceeding' }).id },
  { value: 'rejected', name: defineMessage({ message: 'Rejected' }).id },
  { value: 'closed', name: defineMessage({ message: 'Closed' }).id },
];

export const PROPOSAL_STATUS_GROUP_CHOICES = [
  { value: 'new', name: defineMessage({ message: 'New' }).id },
  { value: 'proceeding', name: defineMessage({ message: 'Proceeding' }).id },
  { value: 'approved', name: defineMessage({ message: 'CV approved' }).id },
  { value: 'rejected', name: defineMessage({ message: 'CV rejected' }).id },
  { value: 'interviewing', name: defineMessage({ message: 'Interviewing' }).id },
  { value: 'offer', name: defineMessage({ message: 'Offer' }).id },
  { value: 'offer_accepted', name: defineMessage({ message: 'Offer Accepted' }).id },
  { value: 'offer_declined', name: defineMessage({ message: 'Offer Declined' }).id },
  { value: 'candidate_quit', name: `Candidate Quits Process` },
  { value: 'closed', name: defineMessage({ message: 'Closed' }).id },
];

export const SALARY_CURRENCY_CHOICES = [
  {
    value: 'JPY',
    description: defineMessage({ message: '¥ Japanese Yen' }).id,
    name: '¥',
  },
  {
    value: 'USD',
    description: defineMessage({ message: '$ US Dollar' }).id,
    name: '$',
  },
  { value: 'EUR', description: defineMessage({ message: '€ Euro' }).id, name: '€' },
  {
    value: 'CNY',
    description: defineMessage({ message: '¥ Chinese Yuan Renminbi' }).id,
    name: '¥',
  },
  {
    value: 'GBP',
    description: defineMessage({ message: '£ British Pound' }).id,
    name: '£',
  },
  {
    value: 'KRW',
    description: defineMessage({ message: '₩ South Korean Won' }).id,
    name: '₩',
  },
  {
    value: 'INR',
    description: defineMessage({ message: '₹ Indian Rupee' }).id,
    name: '₹',
  },
  {
    value: 'CAD',
    description: defineMessage({ message: 'C$ Canadian Dollar' }).id,
    name: 'C$',
  },
  {
    value: 'HKD',
    description: defineMessage({ message: 'HK$ Hong Kong Dollar' }).id,
    name: 'HK$',
  },
  {
    value: 'BRL',
    description: defineMessage({ message: 'R$ Brazilian Real' }).id,
    name: 'R$',
  },
];

export const SALARY_PER_CHOICES = [
  { value: 'year', name: defineMessage({ message: 'Year' }).id },
  { value: 'month', name: defineMessage({ message: 'Month' }).id },
  { value: 'week', name: defineMessage({ message: 'Week' }).id },
  { value: 'day', name: defineMessage({ message: 'Day' }).id },
  { value: 'hour', name: defineMessage({ message: 'Hour' }).id },
];

export const LOCALE_CHOICES = [
  { value: 'en', name: 'English', transKey: defineMessage({ message: 'English' }).id },
  { value: 'ja', name: '日本語', transKey: defineMessage({ message: 'Japanese' }).id },
];

export const LANGUAGE_CHOICES = [
  { value: 'en', name: defineMessage({ message: 'English' }).id },
  { value: 'ja', name: defineMessage({ message: 'Japanese' }).id },
  { value: 'ar', name: defineMessage({ message: 'Arabic' }).id },
  { value: 'bn', name: defineMessage({ message: 'Bengali' }).id },
  { value: 'fr', name: defineMessage({ message: 'French' }).id },
  { value: 'de', name: defineMessage({ message: 'German' }).id },
  { value: 'hi', name: defineMessage({ message: 'Hindi' }).id },
  { value: 'it', name: defineMessage({ message: 'Italian' }).id },
  { value: 'jv', name: defineMessage({ message: 'Javanese' }).id },
  { value: 'ko', name: defineMessage({ message: 'Korean' }).id },
  { value: 'lah', name: defineMessage({ message: 'Lahnda' }).id },
  { value: 'zlm', name: defineMessage({ message: 'Malay' }).id },
  { value: 'cmn', name: defineMessage({ message: 'Mandarin Chinese' }).id },
  { value: 'mr', name: defineMessage({ message: 'Marathi' }).id },
  { value: 'pt', name: defineMessage({ message: 'Portuguese' }).id },
  { value: 'ru', name: defineMessage({ message: 'Russian' }).id },
  { value: 'wu', name: defineMessage({ message: 'Shanghainese' }).id },
  { value: 'es', name: defineMessage({ message: 'Spanish' }).id },
  { value: 'ta', name: defineMessage({ message: 'Tamil' }).id },
  { value: 'te', name: defineMessage({ message: 'Telugu' }).id },
  { value: 'th', name: defineMessage({ message: 'Thai' }).id },
  { value: 'tr', name: defineMessage({ message: 'Turkish' }).id },
  { value: 'ur', name: defineMessage({ message: 'Urdu' }).id },
  { value: 'vi', name: defineMessage({ message: 'Vietnamese' }).id },
  { value: 'yue', name: defineMessage({ message: 'Yue Chinese' }).id },
];

export const LANGUAGE_LEVEL_CHOICES = [
  { value: 0, name: defineMessage({ message: 'Survival' }).id },
  { value: 1, name: defineMessage({ message: 'Daily Conversation' }).id },
  { value: 2, name: defineMessage({ message: 'Advanced' }).id },
  { value: 3, name: defineMessage({ message: 'Fluent' }).id },
  { value: 4, name: defineMessage({ message: 'Native' }).id },
];

export const EMPLOYMENT_CHOICES = [
  { value: 'businessowner', name: defineMessage({ message: 'Business Owner' }).id },
  { value: 'fulltime', name: defineMessage({ message: 'Permanent Employee' }).id },
  {
    value: 'fixedterm',
    name: defineMessage({ message: 'Fixed-term Contract Employee' }).id,
  },
  { value: 'temporary', name: defineMessage({ message: 'Part-time Employee' }).id },
  { value: 'dispatched', name: defineMessage({ message: 'Dispatched' }).id },
  { value: 'freelance', name: defineMessage({ message: 'Freelance' }).id },
  { value: 'notemployed', name: defineMessage({ message: 'Unemployed' }).id },
];

export const JOB_EMPLOYMENT_TYPE_CHOICES = [
  { value: 'permanent', name: defineMessage({ message: 'Permanent Employee' }).id },
  { value: 'parttime', name: defineMessage({ message: 'Part Time Employee' }).id },
  {
    value: 'fixedterm',
    name: defineMessage({ message: 'Fixed Term Contract Employee' }).id,
  },
  { value: 'dispatch', name: defineMessage({ message: 'Dispatch' }).id },
  { value: 'freelance', name: defineMessage({ message: 'Freelance' }).id },
];

export const JOB_FLEXTIME_ELIGIBILITY_CHOICES = [
  { value: 'eligible', name: defineMessage({ message: 'Eligible' }).id },
  { value: 'not_eligible', name: defineMessage({ message: 'Not Eligible' }).id },
];

export const JOB_TELEWORK_ELIGIBILITY_CHOICES = [
  { value: 'onsite', name: defineMessage({ message: 'On Site Only' }).id },
  { value: 'possible', name: defineMessage({ message: 'Remote Possible' }).id },
  { value: 'remote', name: defineMessage({ message: 'Remote Only' }).id },
];

export const PIPELINE_ITEMS_CHOICES = [
  { value: 'associated', name: defineMessage({ message: 'Associated' }).id },
  { value: 'preScreening', name: defineMessage({ message: 'Pre-Screening' }).id },
  { value: 'screening', name: defineMessage({ message: 'Screening' }).id },
  { value: 'submissions', name: defineMessage({ message: 'Submissions' }).id },
  { value: 'interviewing', name: defineMessage({ message: 'Interviewing' }).id },
  { value: 'offering', name: defineMessage({ message: 'Оffering' }).id },
  { value: 'hired', name: defineMessage({ message: 'Hired' }).id },
  { value: 'rejected', name: defineMessage({ message: 'Rejected' }).id },
];

export const INTERVIEW_ITEMS_CHOICES = [
  { value: 'final_interview', name: defineMessage({ message: 'Final Interview' }).id },
  { value: 'in_process', name: defineMessage({ message: 'In Process' }).id },
  { value: 'first_interview', name: defineMessage({ message: 'First Interview' }).id },
];

export const REASON_FOR_OPENING_CHOICES = [
  { value: 'replacement', name: defineMessage({ message: 'Replacement' }).id },
  { value: 'new', name: defineMessage({ message: 'New' }).id },
];

export const INTERVIEW_TYPES_CHOICES = [
  { value: 'assignment', name: defineMessage({ message: 'Assignment' }).id },
  { value: 'technical_fit', name: defineMessage({ message: 'Technical Fit' }).id },
  { value: 'cultural_fit', name: defineMessage({ message: 'Cultural Fit' }).id },
  { value: 'general', name: defineMessage({ message: 'General' }).id },
  { value: 'cross_team', name: defineMessage({ message: 'Cross-Team' }).id },
];

export const EDUCATION_LEVELS_CHOICES = [
  { value: 'none', name: defineMessage({ message: 'None' }).id },
  { value: 'highschool', name: defineMessage({ message: 'High School Diploma' }).id },
  { value: 'bachelors', name: defineMessage({ message: "Bachelor's Degree" }).id },
  { value: 'masters', name: defineMessage({ message: "Master's Degree" }).id },
  { value: 'phd', name: defineMessage({ message: 'PhD' }).id },
];

export const SOCIAL_INSURANCES_CHOICES = [
  { value: 'health', name: defineMessage({ message: 'Health Insurance' }).id },
  { value: 'employment', name: defineMessage({ message: 'Employment Insurance' }).id },
  {
    value: 'welfare_pension',
    name: defineMessage({ message: 'Welfare Pension Insurance' }).id,
  },
  {
    value: 'accident_compensation',
    name: defineMessage({ message: 'Workers Accident Compensation Insurance' }).id,
  },
];

export const OTHER_BENEFITS_CHOICES = [
  { value: 'visa', name: defineMessage({ message: 'Visa Sponsorship' }).id },
  { value: 'relocation', name: defineMessage({ message: 'Relocation Assistance' }).id },
  {
    value: 'wellness',
    name: defineMessage({ message: 'Gym / Wellness Membership' }).id,
  },
  { value: 'coffee', name: defineMessage({ message: 'Free Coffee' }).id },
];

export const GENDERS_CHOICES = [
  { value: 'male', name: defineMessage({ message: 'Male' }).id },
  { value: 'female', name: defineMessage({ message: 'Female' }).id },
  { value: 'other', name: defineMessage({ message: 'Other' }).id },
];

export const TAX_EQUALIZATION_CHOICES = [
  { value: true, name: defineMessage({ message: 'Yes' }).id },
  { value: false, name: defineMessage({ message: 'No' }).id },
];

export const CERTIFICATION_CHOICES = [
  { value: 'toeic', name: defineMessage({ message: 'TOEIC' }).id },
  { value: 'jlpt', name: defineMessage({ message: 'JLPT' }).id },
  { value: 'toefl', name: defineMessage({ message: 'TOEFL' }).id },
  { value: 'other', name: defineMessage({ message: 'Other' }).id },
];

export const OTHER_DESIRED_BENEFIT_CHOICES = [
  {
    value: 'sign_on_bonus',
    name: defineMessage({ message: 'One-Time Sign On Bonus' }).id,
  },
  { value: 'relocation', name: defineMessage({ message: 'Relocation' }).id },
  {
    value: 'holidays',
    name: defineMessage({ message: 'Minimum Number of Holidays Per Year' }).id,
  },
  { value: 'schooling', name: defineMessage({ message: 'Schooling for Kids' }).id },
  { value: 'company_car', name: defineMessage({ message: 'Company Car' }).id },
  {
    value: 'training',
    name: defineMessage({ message: 'Company Sponsored Training' }).id,
  },
  { value: 'housing', name: defineMessage({ message: 'Housing Support' }).id },
  { value: 'equity', name: defineMessage({ message: 'Equity' }).id },
  {
    value: 'tax_equalization',
    name: defineMessage({ message: 'Tax Equalization' }).id,
  },
  {
    value: 'special_insurance',
    name: defineMessage({ message: 'Special Insurance' }).id,
  },
  { value: 'other', name: defineMessage({ message: 'Other' }).id },
];

export const JOB_CHANGE_URGENCY_CHOICES = [
  { value: 'urgent', name: defineMessage({ message: 'Urgent' }).id },
  {
    value: 'actively_looking',
    name: defineMessage({ message: 'Actively Looking' }).id,
  },
  {
    value: 'passively_looking',
    name: defineMessage({ message: 'Passively Looking' }).id,
  },
  { value: 'not_looking', name: defineMessage({ message: 'Not Looking' }).id },
];

export const NOTICE_PERIOD_CHOICES = [
  { value: 'immediate', name: defineMessage({ message: 'Immediate' }).id },
  { value: 'two_weeks', name: defineMessage({ message: '2 Weeks' }).id },
  { value: 'one_month', name: defineMessage({ message: '1 Month' }).id },
  { value: 'two_months', name: defineMessage({ message: '2 Months' }).id },
  { value: 'three_months', name: defineMessage({ message: '3+ Months' }).id },
];

export const CANDIDATE_SOURCE_CHOICES = [
  { value: 'Headhunt', name: defineMessage({ message: 'Headhunt' }).id },
  { value: 'Referral', name: defineMessage({ message: 'Referral' }).id },
  { value: 'Direct Apply', name: defineMessage({ message: 'Direct Apply' }).id },
  { value: 'Career Fair', name: defineMessage({ message: 'Career Fair' }).id },
  { value: 'Agency', name: defineMessage({ message: 'Agency' }).id },
  { value: 'Other', name: defineMessage({ message: 'Other' }).id },
];

export const NATIONALITIES_CHOICES = [
  { value: 'Afghan', name: defineMessage({ message: 'Afghan' }).id },
  { value: 'Albanian', name: defineMessage({ message: 'Albanian' }).id },
  { value: 'Algerian', name: defineMessage({ message: 'Algerian' }).id },
  { value: 'American', name: defineMessage({ message: 'American' }).id },
  { value: 'Andorran', name: defineMessage({ message: 'Andorran' }).id },
  { value: 'Angolan', name: defineMessage({ message: 'Angolan' }).id },
  { value: 'Antiguans', name: defineMessage({ message: 'Antiguans' }).id },
  { value: 'Argentinean', name: defineMessage({ message: 'Argentinean' }).id },
  { value: 'Armenian', name: defineMessage({ message: 'Armenian' }).id },
  { value: 'Australian', name: defineMessage({ message: 'Australian' }).id },
  { value: 'Austrian', name: defineMessage({ message: 'Austrian' }).id },
  { value: 'Azerbaijani', name: defineMessage({ message: 'Azerbaijani' }).id },
  { value: 'Bahamian', name: defineMessage({ message: 'Bahamian' }).id },
  { value: 'Bahraini', name: defineMessage({ message: 'Bahraini' }).id },
  { value: 'Bangladeshi', name: defineMessage({ message: 'Bangladeshi' }).id },
  { value: 'Barbadian', name: defineMessage({ message: 'Barbadian' }).id },
  { value: 'Barbudans', name: defineMessage({ message: 'Barbudans' }).id },
  { value: 'Batswana', name: defineMessage({ message: 'Batswana' }).id },
  { value: 'Belarusian', name: defineMessage({ message: 'Belarusian' }).id },
  { value: 'Belgian', name: defineMessage({ message: 'Belgian' }).id },
  { value: 'Belizean', name: defineMessage({ message: 'Belizean' }).id },
  { value: 'Beninese', name: defineMessage({ message: 'Beninese' }).id },
  { value: 'Bhutanese', name: defineMessage({ message: 'Bhutanese' }).id },
  { value: 'Bolivian', name: defineMessage({ message: 'Bolivian' }).id },
  { value: 'Bosnian', name: defineMessage({ message: 'Bosnian' }).id },
  { value: 'Brazilian', name: defineMessage({ message: 'Brazilian' }).id },
  { value: 'British', name: defineMessage({ message: 'British' }).id },
  { value: 'Bruneian', name: defineMessage({ message: 'Bruneian' }).id },
  { value: 'Bulgarian', name: defineMessage({ message: 'Bulgarian' }).id },
  { value: 'Burkinabe', name: defineMessage({ message: 'Burkinabe' }).id },
  { value: 'Burmese', name: defineMessage({ message: 'Burmese' }).id },
  { value: 'Burundian', name: defineMessage({ message: 'Burundian' }).id },
  { value: 'Cambodian', name: defineMessage({ message: 'Cambodian' }).id },
  { value: 'Cameroonian', name: defineMessage({ message: 'Cameroonian' }).id },
  { value: 'Canadian', name: defineMessage({ message: 'Canadian' }).id },
  { value: 'Cape Verdean', name: defineMessage({ message: 'Cape Verdean' }).id },
  { value: 'Central African', name: defineMessage({ message: 'Central African' }).id },
  { value: 'Chadian', name: defineMessage({ message: 'Chadian' }).id },
  { value: 'Chilean', name: defineMessage({ message: 'Chilean' }).id },
  { value: 'Chinese', name: defineMessage({ message: 'Chinese' }).id },
  { value: 'Colombian', name: defineMessage({ message: 'Colombian' }).id },
  { value: 'Comoran', name: defineMessage({ message: 'Comoran' }).id },
  { value: 'Congolese', name: defineMessage({ message: 'Congolese' }).id },
  { value: 'Costa Rican', name: defineMessage({ message: 'Costa Rican' }).id },
  { value: 'Croatian', name: defineMessage({ message: 'Croatian' }).id },
  { value: 'Cuban', name: defineMessage({ message: 'Cuban' }).id },
  { value: 'Cypriot', name: defineMessage({ message: 'Cypriot' }).id },
  { value: 'Czech', name: defineMessage({ message: 'Czech' }).id },
  { value: 'Danish', name: defineMessage({ message: 'Danish' }).id },
  { value: 'Djibouti', name: defineMessage({ message: 'Djibouti' }).id },
  { value: 'Dominican', name: defineMessage({ message: 'Dominican' }).id },
  { value: 'Dutch', name: defineMessage({ message: 'Dutch' }).id },
  { value: 'East Timorese', name: defineMessage({ message: 'East Timorese' }).id },
  { value: 'Ecuadorean', name: defineMessage({ message: 'Ecuadorean' }).id },
  { value: 'Egyptian', name: defineMessage({ message: 'Egyptian' }).id },
  { value: 'Emirian', name: defineMessage({ message: 'Emirian' }).id },
  {
    value: 'Equatorial Guinean',
    name: defineMessage({ message: 'Equatorial Guinean' }).id,
  },
  { value: 'Eritrean', name: defineMessage({ message: 'Eritrean' }).id },
  { value: 'Estonian', name: defineMessage({ message: 'Estonian' }).id },
  { value: 'Ethiopian', name: defineMessage({ message: 'Ethiopian' }).id },
  { value: 'Fijian', name: defineMessage({ message: 'Fijian' }).id },
  { value: 'Filipino', name: defineMessage({ message: 'Filipino' }).id },
  { value: 'Finnish', name: defineMessage({ message: 'Finnish' }).id },
  { value: 'French', name: defineMessage({ message: 'French' }).id },
  { value: 'Gabonese', name: defineMessage({ message: 'Gabonese' }).id },
  { value: 'Gambian', name: defineMessage({ message: 'Gambian' }).id },
  { value: 'Georgian', name: defineMessage({ message: 'Georgian' }).id },
  { value: 'German', name: defineMessage({ message: 'German' }).id },
  { value: 'Ghanaian', name: defineMessage({ message: 'Ghanaian' }).id },
  { value: 'Greek', name: defineMessage({ message: 'Greek' }).id },
  { value: 'Grenadian', name: defineMessage({ message: 'Grenadian' }).id },
  { value: 'Guatemalan', name: defineMessage({ message: 'Guatemalan' }).id },
  { value: 'Guinea-Bissauan', name: defineMessage({ message: 'Guinea-Bissauan' }).id },
  { value: 'Guinean', name: defineMessage({ message: 'Guinean' }).id },
  { value: 'Guyanese', name: defineMessage({ message: 'Guyanese' }).id },
  { value: 'Haitian', name: defineMessage({ message: 'Haitian' }).id },
  { value: 'Herzegovinian', name: defineMessage({ message: 'Herzegovinian' }).id },
  { value: 'Honduran', name: defineMessage({ message: 'Honduran' }).id },
  { value: 'Hungarian', name: defineMessage({ message: 'Hungarian' }).id },
  { value: 'I-Kiribati', name: defineMessage({ message: 'I-Kiribati' }).id },
  { value: 'Icelander', name: defineMessage({ message: 'Icelander' }).id },
  { value: 'Indian', name: defineMessage({ message: 'Indian' }).id },
  { value: 'Indonesian', name: defineMessage({ message: 'Indonesian' }).id },
  { value: 'Iranian', name: defineMessage({ message: 'Iranian' }).id },
  { value: 'Iraqi', name: defineMessage({ message: 'Iraqi' }).id },
  { value: 'Irish', name: defineMessage({ message: 'Irish' }).id },
  { value: 'Israeli', name: defineMessage({ message: 'Israeli' }).id },
  { value: 'Italian', name: defineMessage({ message: 'Italian' }).id },
  { value: 'Ivorian', name: defineMessage({ message: 'Ivorian' }).id },
  { value: 'Jamaican', name: defineMessage({ message: 'Jamaican' }).id },
  { value: 'Japanese', name: defineMessage({ message: 'Japanese' }).id },
  { value: 'Jordanian', name: defineMessage({ message: 'Jordanian' }).id },
  { value: 'Kazakhstani', name: defineMessage({ message: 'Kazakhstani' }).id },
  { value: 'Kenyan', name: defineMessage({ message: 'Kenyan' }).id },
  {
    value: 'Kittian and Nevisian',
    name: defineMessage({ message: 'Kittian and Nevisian' }).id,
  },
  { value: 'Kuwaiti', name: defineMessage({ message: 'Kuwaiti' }).id },
  { value: 'Kyrgyz', name: defineMessage({ message: 'Kyrgyz' }).id },
  { value: 'Laotian', name: defineMessage({ message: 'Laotian' }).id },
  { value: 'Latvian', name: defineMessage({ message: 'Latvian' }).id },
  { value: 'Lebanese', name: defineMessage({ message: 'Lebanese' }).id },
  { value: 'Liberian', name: defineMessage({ message: 'Liberian' }).id },
  { value: 'Libyan', name: defineMessage({ message: 'Libyan' }).id },
  { value: 'Liechtensteiner', name: defineMessage({ message: 'Liechtensteiner' }).id },
  { value: 'Lithuanian', name: defineMessage({ message: 'Lithuanian' }).id },
  { value: 'Luxembourger', name: defineMessage({ message: 'Luxembourger' }).id },
  { value: 'Macedonian', name: defineMessage({ message: 'Macedonian' }).id },
  { value: 'Malagasy', name: defineMessage({ message: 'Malagasy' }).id },
  { value: 'Malawian', name: defineMessage({ message: 'Malawian' }).id },
  { value: 'Malaysian', name: defineMessage({ message: 'Malaysian' }).id },
  { value: 'Maldivian', name: defineMessage({ message: 'Maldivian' }).id },
  { value: 'Malian', name: defineMessage({ message: 'Malian' }).id },
  { value: 'Maltese', name: defineMessage({ message: 'Maltese' }).id },
  { value: 'Marshallese', name: defineMessage({ message: 'Marshallese' }).id },
  { value: 'Mauritanian', name: defineMessage({ message: 'Mauritanian' }).id },
  { value: 'Mauritian', name: defineMessage({ message: 'Mauritian' }).id },
  { value: 'Mexican', name: defineMessage({ message: 'Mexican' }).id },
  { value: 'Micronesian', name: defineMessage({ message: 'Micronesian' }).id },
  { value: 'Moldovan', name: defineMessage({ message: 'Moldovan' }).id },
  { value: 'Monacan', name: defineMessage({ message: 'Monacan' }).id },
  { value: 'Mongolian', name: defineMessage({ message: 'Mongolian' }).id },
  { value: 'Moroccan', name: defineMessage({ message: 'Moroccan' }).id },
  { value: 'Mosotho', name: defineMessage({ message: 'Mosotho' }).id },
  { value: 'Motswana', name: defineMessage({ message: 'Motswana' }).id },
  { value: 'Mozambican', name: defineMessage({ message: 'Mozambican' }).id },
  { value: 'Namibian', name: defineMessage({ message: 'Namibian' }).id },
  { value: 'Nauruan', name: defineMessage({ message: 'Nauruan' }).id },
  { value: 'Nepalese', name: defineMessage({ message: 'Nepalese' }).id },
  { value: 'New Zealander', name: defineMessage({ message: 'New Zealander' }).id },
  { value: 'Ni-Vanuatu', name: defineMessage({ message: 'Ni-Vanuatu' }).id },
  { value: 'Nicaraguan', name: defineMessage({ message: 'Nicaraguan' }).id },
  { value: 'Nigerian', name: defineMessage({ message: 'Nigerian' }).id },
  { value: 'Nigerien', name: defineMessage({ message: 'Nigerien' }).id },
  { value: 'North Korean', name: defineMessage({ message: 'North Korean' }).id },
  { value: 'Northern Irish', name: defineMessage({ message: 'Northern Irish' }).id },
  { value: 'Norwegian', name: defineMessage({ message: 'Norwegian' }).id },
  { value: 'Omani', name: defineMessage({ message: 'Omani' }).id },
  { value: 'Pakistani', name: defineMessage({ message: 'Pakistani' }).id },
  { value: 'Palauan', name: defineMessage({ message: 'Palauan' }).id },
  { value: 'Panamanian', name: defineMessage({ message: 'Panamanian' }).id },
  {
    value: 'Papua New Guinean',
    name: defineMessage({ message: 'Papua New Guinean' }).id,
  },
  { value: 'Paraguayan', name: defineMessage({ message: 'Paraguayan' }).id },
  { value: 'Peruvian', name: defineMessage({ message: 'Peruvian' }).id },
  { value: 'Polish', name: defineMessage({ message: 'Polish' }).id },
  { value: 'Portuguese', name: defineMessage({ message: 'Portuguese' }).id },
  { value: 'Qatari', name: defineMessage({ message: 'Qatari' }).id },
  { value: 'Romanian', name: defineMessage({ message: 'Romanian' }).id },
  { value: 'Russian', name: defineMessage({ message: 'Russian' }).id },
  { value: 'Rwandan', name: defineMessage({ message: 'Rwandan' }).id },
  { value: 'Saint Lucian', name: defineMessage({ message: 'Saint Lucian' }).id },
  { value: 'Salvadoran', name: defineMessage({ message: 'Salvadoran' }).id },
  { value: 'Samoan', name: defineMessage({ message: 'Samoan' }).id },
  { value: 'San Marinese', name: defineMessage({ message: 'San Marinese' }).id },
  { value: 'Sao Tomean', name: defineMessage({ message: 'Sao Tomean' }).id },
  { value: 'Saudi', name: defineMessage({ message: 'Saudi' }).id },
  { value: 'Scottish', name: defineMessage({ message: 'Scottish' }).id },
  { value: 'Senegalese', name: defineMessage({ message: 'Senegalese' }).id },
  { value: 'Serbian', name: defineMessage({ message: 'Serbian' }).id },
  { value: 'Seychellois', name: defineMessage({ message: 'Seychellois' }).id },
  { value: 'Sierra Leonean', name: defineMessage({ message: 'Sierra Leonean' }).id },
  { value: 'Singaporean', name: defineMessage({ message: 'Singaporean' }).id },
  { value: 'Slovakian', name: defineMessage({ message: 'Slovakian' }).id },
  { value: 'Slovenian', name: defineMessage({ message: 'Slovenian' }).id },
  {
    value: 'Solomon Islander',
    name: defineMessage({ message: 'Solomon Islander' }).id,
  },
  { value: 'Somali', name: defineMessage({ message: 'Somali' }).id },
  { value: 'South African', name: defineMessage({ message: 'South African' }).id },
  { value: 'South Korean', name: defineMessage({ message: 'South Korean' }).id },
  { value: 'Spanish', name: defineMessage({ message: 'Spanish' }).id },
  { value: 'Sri Lankan', name: defineMessage({ message: 'Sri Lankan' }).id },
  { value: 'Sudanese', name: defineMessage({ message: 'Sudanese' }).id },
  { value: 'Surinamer', name: defineMessage({ message: 'Surinamer' }).id },
  { value: 'Swazi', name: defineMessage({ message: 'Swazi' }).id },
  { value: 'Swedish', name: defineMessage({ message: 'Swedish' }).id },
  { value: 'Swiss', name: defineMessage({ message: 'Swiss' }).id },
  { value: 'Syrian', name: defineMessage({ message: 'Syrian' }).id },
  { value: 'Taiwanese', name: defineMessage({ message: 'Taiwanese' }).id },
  { value: 'Tajik', name: defineMessage({ message: 'Tajik' }).id },
  { value: 'Tanzanian', name: defineMessage({ message: 'Tanzanian' }).id },
  { value: 'Thai', name: defineMessage({ message: 'Thai' }).id },
  { value: 'Togolese', name: defineMessage({ message: 'Togolese' }).id },
  { value: 'Tongan', name: defineMessage({ message: 'Tongan' }).id },
  {
    value: 'Trinidadian or Tobagonian',
    name: defineMessage({ message: 'Trinidadian or Tobagonian' }).id,
  },
  { value: 'Tunisian', name: defineMessage({ message: 'Tunisian' }).id },
  { value: 'Turkish', name: defineMessage({ message: 'Turkish' }).id },
  { value: 'Tuvaluan', name: defineMessage({ message: 'Tuvaluan' }).id },
  { value: 'Ugandan', name: defineMessage({ message: 'Ugandan' }).id },
  { value: 'Ukrainian', name: defineMessage({ message: 'Ukrainian' }).id },
  { value: 'Uruguayan', name: defineMessage({ message: 'Uruguayan' }).id },
  { value: 'Uzbekistani', name: defineMessage({ message: 'Uzbekistani' }).id },
  { value: 'Venezuelan', name: defineMessage({ message: 'Venezuelan' }).id },
  { value: 'Vietnamese', name: defineMessage({ message: 'Vietnamese' }).id },
  { value: 'Welsh', name: defineMessage({ message: 'Welsh' }).id },
  { value: 'Yemenite', name: defineMessage({ message: 'Yemenite' }).id },
  { value: 'Zambian', name: defineMessage({ message: 'Zambian' }).id },
  { value: 'Zimbabwean', name: defineMessage({ message: 'Zimbabwean' }).id },
];

export const PLATFORM_CHOICES = [
  { value: 'linkedin', name: defineMessage({ message: 'LinkedIn' }).id },
  { value: 'facebook', name: defineMessage({ message: 'Facebook' }).id },
  { value: 'biz_reach', name: defineMessage({ message: 'Biz Reach' }).id },
  { value: 'github', name: defineMessage({ message: 'Github' }).id },
  { value: 'careercross', name: defineMessage({ message: 'CareerCross' }).id },
  {
    value: 'corporate_website',
    name: defineMessage({ message: 'Corporate Website' }).id,
  },
  { value: 'other', name: defineMessage({ message: 'Other' }).id },
];

export const DECISION_CHOICES = [
  { value: 'proceed', name: defineMessage({ message: 'Proceed' }).id },
  { value: 'keep', name: defineMessage({ message: 'Keep' }).id },
  { value: 'reject', name: defineMessage({ message: 'Reject' }).id },
];
