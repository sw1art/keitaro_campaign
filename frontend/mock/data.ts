import type { Campaign, Domain, GeoCountry, Offer, Operation, OperationStage, Stream, TrafficSource } from '~/types'

function pad(value: number): string {
  return String(value).padStart(2, '0')
}

export function dbDate(date: Date): string {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

export function isoDate(date: Date): string {
  return date.toISOString()
}

function minutesAgo(minutes: number): Date {
  return new Date(Date.now() - minutes * 60_000)
}

export const GEO: GeoCountry[] = [
  { code: 'AU', name: 'Australia' },
  { code: 'AT', name: 'Austria' },
  { code: 'BE', name: 'Belgium' },
  { code: 'BR', name: 'Brazil' },
  { code: 'CA', name: 'Canada' },
  { code: 'CZ', name: 'Czechia' },
  { code: 'DK', name: 'Denmark' },
  { code: 'FI', name: 'Finland' },
  { code: 'FR', name: 'France' },
  { code: 'DE', name: 'Germany' },
  { code: 'GR', name: 'Greece' },
  { code: 'HU', name: 'Hungary' },
  { code: 'IN', name: 'India' },
  { code: 'ID', name: 'Indonesia' },
  { code: 'IE', name: 'Ireland' },
  { code: 'IL', name: 'Israel' },
  { code: 'IT', name: 'Italy' },
  { code: 'JP', name: 'Japan' },
  { code: 'MX', name: 'Mexico' },
  { code: 'NL', name: 'Netherlands' },
  { code: 'NZ', name: 'New Zealand' },
  { code: 'NO', name: 'Norway' },
  { code: 'PE', name: 'Peru' },
  { code: 'PH', name: 'Philippines' },
  { code: 'PL', name: 'Poland' },
  { code: 'PT', name: 'Portugal' },
  { code: 'RO', name: 'Romania' },
  { code: 'SG', name: 'Singapore' },
  { code: 'ZA', name: 'South Africa' },
  { code: 'KR', name: 'South Korea' },
  { code: 'ES', name: 'Spain' },
  { code: 'SE', name: 'Sweden' },
  { code: 'CH', name: 'Switzerland' },
  { code: 'TH', name: 'Thailand' },
  { code: 'TR', name: 'Turkey' },
  { code: 'UA', name: 'Ukraine' },
  { code: 'AE', name: 'United Arab Emirates' },
  { code: 'GB', name: 'United Kingdom' },
  { code: 'US', name: 'United States' },
  { code: 'VN', name: 'Vietnam' },
]

export const OFFERS: Offer[] = [
  { id: 25327, name: '25327 Flexacil', state: 'active', country: ['PE'], group: 'JO Flexacil PE', affiliate_network: '59' },
  { id: 25328, name: '25328 Cardioton', state: 'active', country: ['PL'], group: 'JO Cardioton PL', affiliate_network: '12' },
  { id: 25329, name: '25329 Prostex', state: 'active', country: ['RO'], group: 'JO Prostex RO', affiliate_network: '34' },
  { id: 25330, name: '25330 Neuroton', state: 'active', country: ['MX'], group: 'JO Neuroton MX', affiliate_network: '59' },
  { id: 25331, name: '25331 Vitaslim', state: 'active', country: ['DE'], group: 'JO Vitaslim DE', affiliate_network: '7' },
  { id: 25332, name: '25332 Arterin', state: 'active', country: ['AU'], group: 'JO Arterin AU', affiliate_network: '59' },
  { id: 25333, name: '25333 Ostelife', state: 'active', country: ['ES'], group: 'JO Ostelife ES', affiliate_network: '34' },
  { id: 25334, name: '25334 Prostatricum', state: 'active', country: ['IT'], group: 'JO Prostatricum IT', affiliate_network: '12' },
  { id: 25335, name: '25335 Diabextan', state: 'active', country: ['TR'], group: 'JO Diabextan TR', affiliate_network: '7' },
  { id: 25336, name: '25336 Renovix', state: 'active', country: ['CZ'], group: 'JO Renovix CZ', affiliate_network: '59' },
  { id: 25337, name: '25337 Flexacil Plus', state: 'active', country: ['BR'], group: 'JO Flexacil BR', affiliate_network: '59' },
  { id: 25338, name: '25338 Cardiovax', state: 'disabled', country: ['FR'], group: 'JO Cardiovax FR', affiliate_network: '34' },
  { id: 25339, name: '25339 Visonorm', state: 'active', country: ['GB'], group: 'JO Visonorm GB', affiliate_network: '12' },
  { id: 25340, name: '25340 Cholestin', state: 'disabled', country: ['US'], group: 'JO Cholestin US', affiliate_network: '7' },
  { id: 25341, name: '25341 Normaten', state: 'active', country: ['IN'], group: 'JO Normaten IN', affiliate_network: '59' },
  { id: 25342, name: '25342 Glucofit', state: 'active', country: ['PH'], group: 'JO Glucofit PH', affiliate_network: '34' },
  { id: 25343, name: '25343 Hepatoclin', state: 'active', country: ['VN'], group: 'JO Hepatoclin VN', affiliate_network: '12' },
  { id: 25344, name: '25344 OsteoFlex', state: 'active', country: ['UA'], group: 'JO OsteoFlex UA', affiliate_network: '7' },
]

export const DOMAINS: Domain[] = [
  { id: 1813, name: 'kylovoa.com', state: 'active', is_ssl: true, ssl_status: 'issued' },
  { id: 1814, name: 'track.example.com', state: 'active', is_ssl: true, ssl_status: 'issued' },
  { id: 1815, name: 'go.adrobot.io', state: 'active', is_ssl: true, ssl_status: 'issued' },
  { id: 1816, name: 'land.adrobot.io', state: 'active', is_ssl: true, ssl_status: 'issued' },
  { id: 1817, name: 'old-domain.com', state: 'disabled', is_ssl: false, ssl_status: 'none' },
  { id: 1818, name: 'beta.adrobot.io', state: 'active', is_ssl: false, ssl_status: 'pending' },
]

export const TRAFFIC_SOURCES: TrafficSource[] = [
  { id: 836, name: 'FORTESTS', state: 'active' },
  { id: 837, name: 'Google Ads', state: 'active' },
  { id: 838, name: 'Facebook', state: 'disabled' },
]

export function makeCampaigns(): Campaign[] {
  const rows: Array<[name: string, state: string, minutes: number, domainName: string]> = [
    ['test_petrov_qa_create_1', 'active', 12, 'kylovoa.com'],
    ['AdRobot Flexacil PE', 'active', 45, 'go.adrobot.io'],
    ['AdRobot Cardioton PL', 'active', 120, 'land.adrobot.io'],
    ['AdRobot Prostex RO', 'active', 300, 'kylovoa.com'],
    ['Campaign paused demo', 'disabled', 480, 'go.adrobot.io'],
    ['AdRobot Neuroton MX', 'active', 720, 'land.adrobot.io'],
    ['AdRobot Vitaslim DE', 'active', 900, 'kylovoa.com'],
    ['AdRobot Arterin AU', 'disabled', 1200, 'go.adrobot.io'],
    ['AdRobot Ostelife ES', 'active', 1600, 'land.adrobot.io'],
    ['AdRobot Diabextan TR', 'active', 2000, 'kylovoa.com'],
    ['AdRobot Renovix CZ', 'active', 2400, 'go.adrobot.io'],
    ['AdRobot Visonorm GB', 'active', 2880, 'land.adrobot.io'],
  ]

  return rows.map((row, index) => {
    const [name, state, minutes, domainName] = row
    const campaignId = 212150 + index
    const domain = DOMAINS.find((d) => d.name === domainName) ?? DOMAINS[0]
    const created = minutesAgo(minutes)
    const updated = new Date(created.getTime() + 5 * 60_000)
    return {
      id: campaignId,
      name,
      state,
      alias: `alias-${campaignId}`,
      domain: `https://${domain.name}/`,
      domain_id: domain.id,
      traffic_source_id: 836,
      traffic_source: 'FORTESTS',
      group_id: 10332,
      group: 'FORTESTS',
      cost_type: 'CPC',
      cost_value: 0,
      cost_currency: 'USD',
      created_at: dbDate(created),
      updated_at: dbDate(updated),
    }
  })
}

function mockFingerprint(offers: Array<{ offer_id: number; share: number }>): string {
  return offers
    .map((offer) => `${offer.offer_id}:${offer.share}`)
    .sort()
    .join('|')
}

export function makeStreams(
  campaign: Campaign,
  offerIds: number[],
  startStreamId: number,
): { streams: Stream[]; nextStreamId: number } {
  const googleRedirect: Stream = {
    id: startStreamId,
    type: 'regular',
    name: 'Google Redirect',
    campaign_id: campaign.id,
    position: 1,
    state: 'active',
    schema: 'redirect',
    action_type: 'http',
    action_payload: 'https://google.com',
    collect_clicks: true,
    filter_or: false,
    weight: 0,
    offer_selection: 'before_click',
    filters: [{ name: 'country', mode: 'accept', payload: ['AU', 'MX', 'RO'] }],
    offers: [],
    landings: [],
    fingerprint: mockFingerprint([]),
  }

  const flowOffers = offerIds.map((offerId) => ({ offer_id: offerId, state: 'active', share: 100 }))
  const offerFlow: Stream = {
    id: startStreamId + 1,
    type: 'regular',
    name: 'Offer Flow',
    campaign_id: campaign.id,
    position: 2,
    state: 'active',
    schema: 'landings',
    action_type: 'http',
    action_payload: '',
    collect_clicks: true,
    filter_or: false,
    weight: 0,
    offer_selection: 'before_click',
    filters: [],
    offers: flowOffers,
    landings: [],
    fingerprint: mockFingerprint(flowOffers),
  }

  return { streams: [googleRedirect, offerFlow], nextStreamId: startStreamId + 2 }
}

function stageProgress(stage: OperationStage): number {
  switch (stage) {
    case 'pending':
      return 0
    case 'creating_campaign':
      return 15
    case 'creating_google_stream':
      return 40
    case 'creating_offer_stream':
      return 65
    case 'verifying':
      return 90
    case 'completed':
      return 100
    default:
      return 0
  }
}

export function makeOperations(): Operation[] {
  const completed = (operationId: string, campaignId: number, minutes: number): Operation => ({
    operation_id: operationId,
    type: 'campaign.create',
    status: 'completed',
    campaign_id: campaignId,
    error: null,
    current_stage: 'completed',
    progress: 100,
    started_at: isoDate(minutesAgo(minutes - 1)),
    finished_at: isoDate(minutesAgo(minutes - 2)),
    created_at: isoDate(minutesAgo(minutes)),
    completed_at: isoDate(minutesAgo(minutes - 2)),
  })

  const failed = (
    operationId: string,
    code: string,
    message: string,
    minutes: number,
    stage: OperationStage,
  ): Operation => ({
    operation_id: operationId,
    type: 'campaign.create',
    status: 'failed',
    campaign_id: null,
    error: { code, message },
    current_stage: stage,
    progress: stageProgress(stage),
    started_at: isoDate(minutesAgo(minutes - 1)),
    finished_at: isoDate(minutesAgo(minutes - 2)),
    created_at: isoDate(minutesAgo(minutes)),
    completed_at: isoDate(minutesAgo(minutes - 2)),
  })

  return [
    completed('op-seed-1', 212150, 12),
    failed('op-seed-2', 'KEITARO_STREAM_CREATION_FAILED', 'Failed to create Offer Flow', 30, 'creating_offer_stream'),
    completed('op-seed-3', 212151, 45),
    completed('op-seed-4', 212152, 120),
    failed('op-seed-5', 'KEITARO_CAMPAIGN_CREATION_FAILED', 'Keitaro API unavailable', 200, 'creating_campaign'),
    completed('op-seed-6', 212153, 300),
  ]
}
