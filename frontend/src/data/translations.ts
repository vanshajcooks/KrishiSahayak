/**
 * Bilingual Agricultural Dictionary (English & Hindi)
 * Simple and accessible terminology for farmers.
 */

import { AppLanguage } from '@/types/farm';

export interface TranslationDict {
  appTitle: string;
  myFarm: string;
  crop: string;
  field: string;
  status: string;
  cropHealth: string;
  soilMoisture: string;
  irrigationAdvice: string;
  weather: string;
  fieldRisks: string;
  recommendedAction: string;
  actionRequired: string;
  scanCrop: string;
  scanCropSub: string;
  viewDetails: string;
  viewFullAdvice: string;
  markAsDone: string;
  waterStress: string;
  heatStress: string;
  diseaseRisk: string;
  low: string;
  medium: string;
  high: string;
  healthy: string;
  good: string;
  needsAttention: string;
  critical: string;
  deviceConnected: string;
  deviceOffline: string;
  demoMode: string;
  realMode: string;
  home: string;
  scan: string;
  fieldNav: string;
  alerts: string;
  settings: string;
  askAssistant: string;
}

export const translations: Record<AppLanguage, TranslationDict> = {
  en: {
    appTitle: 'Farm Assistant',
    myFarm: 'My Farm',
    crop: 'Crop',
    field: 'Field',
    status: 'Status',
    cropHealth: 'Crop Health',
    soilMoisture: 'Soil Moisture',
    irrigationAdvice: 'Irrigation Advice',
    weather: 'Weather Forecast',
    fieldRisks: 'Field Risks',
    recommendedAction: 'Recommended Action',
    actionRequired: 'ACTION REQUIRED',
    scanCrop: 'Scan Your Crop',
    scanCropSub: 'Take a clear photo of the leaf or plant',
    viewDetails: 'View Details',
    viewFullAdvice: 'View Full Advice',
    markAsDone: 'Mark as Done',
    waterStress: 'Water Stress',
    heatStress: 'Heat Stress',
    diseaseRisk: 'Disease Risk',
    low: 'LOW',
    medium: 'MEDIUM',
    high: 'HIGH',
    healthy: 'Healthy',
    good: 'Good',
    needsAttention: 'Needs Attention',
    critical: 'Critical',
    deviceConnected: 'Device Connected (Live)',
    deviceOffline: 'Device Offline',
    demoMode: 'Demo Mode (Simulated)',
    realMode: 'Live Field Mode',
    home: 'Home',
    scan: 'Scan',
    fieldNav: 'Field',
    alerts: 'Alerts',
    settings: 'Settings',
    askAssistant: 'Ask Farm Assistant',
  },
  hi: {
    appTitle: 'कृषि सहायक',
    myFarm: 'मेरा खेत',
    crop: 'फसल',
    field: 'खेत',
    status: 'स्थिति',
    cropHealth: 'फसल का स्वास्थ्य',
    soilMoisture: 'मिट्टी की नमी',
    irrigationAdvice: 'सिंचाई की सलाह',
    weather: 'मौसम पूर्वानुमान',
    fieldRisks: 'खेत के जोखिम',
    recommendedAction: 'सुझाई गई कार्रवाई',
    actionRequired: 'कार्रवाई आवश्यक',
    scanCrop: 'फसल की जांच करें',
    scanCropSub: 'पत्ती या पौधे की साफ फोटो लें',
    viewDetails: 'विवरण देखें',
    viewFullAdvice: 'पूरी सलाह देखें',
    markAsDone: 'पूर्ण चिह्नित करें',
    waterStress: 'पानी की कमी',
    heatStress: 'गर्मी का तनाव',
    diseaseRisk: 'रोग का खतरा',
    low: 'कम',
    medium: 'मध्यम',
    high: 'अधिक',
    healthy: 'स्वस्थ',
    good: 'अच्छा',
    needsAttention: 'ध्यान दें',
    critical: 'गंभीर',
    deviceConnected: 'डिवाइस कनेक्टेड (लाइव)',
    deviceOffline: 'डिवाइस ऑफलाइन',
    demoMode: 'डेमो मोड (अनुकरण)',
    realMode: 'लाइव खेत मोड',
    home: 'होम',
    scan: 'स्कैन',
    fieldNav: 'खेत',
    alerts: 'सूचनाएं',
    settings: 'सेटिंग्स',
    askAssistant: 'कृषि सहायक से पूछें',
  },
};
