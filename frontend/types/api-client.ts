import type { CampaignListParams, ListResponse, OfferListParams, OperationListParams } from './api'
import type { AuditLogItem } from './audit'
import type { Campaign, CreateCampaignRequest, CreateCampaignResponse } from './campaign'
import type { Dashboard } from './dashboard'
import type { Domain } from './domain'
import type { GeoCountry } from './geo'
import type { Offer } from './offer'
import type { Operation } from './operation'
import type { Stream, UpdateStreamOffersRequest } from './stream'
import type { TrafficSource } from './traffic-source'

/**
 * The contract implemented by both the real HTTP client and the in-browser mock.
 * Endpoints and payloads follow docs/api.md exactly.
 */
export interface AdRobotApi {
  listCampaigns(params?: CampaignListParams): Promise<ListResponse<Campaign>>
  getCampaign(id: number): Promise<Campaign>
  getCampaignStreams(id: number): Promise<Stream[]>
  createCampaign(body: CreateCampaignRequest): Promise<CreateCampaignResponse>
  getStream(id: number): Promise<Stream>
  updateStreamOffers(id: number, body: UpdateStreamOffersRequest): Promise<Stream>
  listOperations(params?: OperationListParams): Promise<ListResponse<Operation>>
  getOperation(id: string): Promise<Operation>
  retryOperation(id: string): Promise<Operation>
  getOperationAudit(id: string): Promise<AuditLogItem[]>
  getDashboard(): Promise<Dashboard>
  listGeo(): Promise<GeoCountry[]>
  listOffers(params?: OfferListParams): Promise<ListResponse<Offer>>
  listDomains(): Promise<Domain[]>
  listTrafficSources(): Promise<TrafficSource[]>
}
