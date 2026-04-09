import { createSlice } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';

interface FilterState {
  timeRange: string;
  riskLevel: string;
}

const initialState: FilterState = {
  timeRange: '24h',
  riskLevel: 'all',
};

const filterSlice = createSlice({
  name: 'filter',
  initialState,
  reducers: {
    setTimeRange: (state, action: PayloadAction<string>) => {
      state.timeRange = action.payload;
    },
    setRiskLevel: (state, action: PayloadAction<string>) => {
      state.riskLevel = action.payload;
    },
  },
});

export const { setTimeRange, setRiskLevel } = filterSlice.actions;
export default filterSlice.reducer;