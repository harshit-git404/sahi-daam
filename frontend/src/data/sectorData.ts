export interface SectorOption {
  id: string;
  name: string;
  description: string;
  icon: string;
  components: string[];
}

export const SECTOR_OPTIONS: SectorOption[] = [
  {
    id: 'food-agriculture',
    name: 'Food & Agriculture',
    description: 'Check fresh produce quality and food-system data.',
    icon: 'eco',
    components: [
      'Fresh fruits & vegetables',
      'Consumer food waste',
      'Post-harvest supply chain losses',
      'Agricultural fertilizers and pesticides',
      'Food packaging and single-use containers',
    ],
  },
  {
    id: 'energy-fuels',
    name: 'Energy & Fuels',
    description: 'Explore fuel, electricity, and renewable-energy data.',
    icon: 'bolt',
    components: [
      'Fossil fuels like petrol, diesel, and coal',
      'Inefficient fossil fuel subsidies',
      'Renewable energy systems like solar and wind',
      'Industrial and residential electricity grid use',
    ],
  },
  {
    id: 'water-resources',
    name: 'Water Resources',
    description: 'Review water supply, irrigation, and wastewater data.',
    icon: 'water_drop',
    components: [
      'Industrial wastewater and factory effluents',
      'Agricultural irrigation water',
      'Municipal and domestic drinking water supply',
    ],
  },
  {
    id: 'consumer-goods-electronics',
    name: 'Consumer Goods & Electronics',
    description: 'Analyze electronics, textiles, plastics, and durable goods.',
    icon: 'devices',
    components: [
      'E-waste like smartphones, laptops, and batteries',
      'Fast fashion textiles and chemical clothing dyes',
      'Single-use plastics like grocery bags and straws',
      'Durable goods like appliances and furniture',
    ],
  },
  {
    id: 'chemicals-hazardous-materials',
    name: 'Chemicals & Hazardous Materials',
    description: 'Review industrial, household, and heavy-metal records.',
    icon: 'science',
    components: [
      'Industrial solvents, paints, and manufacturing toxins',
      'Household chemical cleaners and non-biodegradable detergents',
      'Heavy metals like mercury, lead, and cadmium',
    ],
  },
  {
    id: 'raw-materials-infrastructure',
    name: 'Raw Materials & Infrastructure',
    description: 'Explore construction, mining, and aggregate data.',
    icon: 'construction',
    components: [
      'Construction materials like concrete, cement, and steel',
      'Mined tech minerals like lithium, cobalt, and copper',
      'Aggregates like sand, gravel, and crushed stone',
    ],
  },
  {
    id: 'services-corporate-operations',
    name: 'Services & Corporate Operations',
    description: 'Review procurement, ESG, tourism, and hospitality data.',
    icon: 'business_center',
    components: [
      'Public procurement items and green government contracts',
      'Corporate sustainability and ESG reporting data',
      'Tourism services, hospitality waste, and eco-travel footprints',
    ],
  },
];

export const FOOD_SECTOR_ID = 'food-agriculture';
export const FRESH_PRODUCE_COMPONENT = 'Fresh fruits & vegetables';
