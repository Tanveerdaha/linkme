import api from "@/services/api";
import type { PageResult, UserSearchResult } from "@/types";

export async function searchUsers(params: {
  q?: string;
  location?: string;
  interest?: string;
  page?: number;
  page_size?: number;
}): Promise<PageResult<UserSearchResult>> {
  const { data } = await api.get<PageResult<UserSearchResult>>("/search/users/", {
    params: {
      ...(params.q ? { q: params.q } : {}),
      ...(params.location ? { location: params.location } : {}),
      ...(params.interest ? { interest: params.interest } : {}),
      ...(params.page ? { page: params.page } : {}),
      ...(params.page_size ? { page_size: params.page_size } : {}),
    },
  });
  return data;
}
