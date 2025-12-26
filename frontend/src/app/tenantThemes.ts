/* `frontend/src/app/tenantThemes.ts` */
export const DEFAULT_TENANT = "0486";

export function resolveTenant(): string {
    // Later you can switch to hostname mapping, e.g. subdomain -> tenant
    return DEFAULT_TENANT;
}

export function themeHrefForTenant(tenant: string): string {
    // Served from `public/themes/<tenant>.css`
    return `/themes/${encodeURIComponent(tenant)}.css`;
}
