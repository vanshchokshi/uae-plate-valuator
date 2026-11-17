import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  Text,
  View,
  FlatList,
  ActivityIndicator,
  StatusBar,
  RefreshControl,
  TouchableOpacity,
  TextInput,
  Linking,
  ScrollView
} from 'react-native';
import { SafeAreaView, SafeAreaProvider } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_BASE_URL } from './src/config';

const EMIRATES = ['Dubai', 'Abu Dhabi', 'Sharjah'];
const RECENT_SEARCHES_STORAGE_KEY = '@uae_plate_recent_searches_v2';
const BROKER_WHATSAPP_NUMBER = '971500000000'; // UAE brokerage inquiry hotline

export default function App() {
  const [plates, setPlates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const [selectedEmirate, setSelectedEmirate] = useState('Dubai');
  const [valCode, setValCode] = useState('');
  const [valPlate, setValPlate] = useState('');
  const [valuationResult, setValuationResult] = useState(null);
  const [valLoading, setValLoading] = useState(false);
  const [valError, setValError] = useState('');
  const [recentSearches, setRecentSearches] = useState([]);

  // Load recent searches from AsyncStorage on mount
  useEffect(() => {
    loadRecentSearches();
    fetchComps();
  }, [selectedEmirate]);

  const loadRecentSearches = async () => {
    try {
      const stored = await AsyncStorage.getItem(RECENT_SEARCHES_STORAGE_KEY);
      if (stored) {
        setRecentSearches(JSON.parse(stored));
      }
    } catch (e) {
      console.warn('Failed to load recent searches from AsyncStorage', e);
    }
  };

  const saveRecentSearch = async (newEntry) => {
    try {
      setRecentSearches((prev) => {
        const filtered = prev.filter(
          (item) => item.plate_display !== newEntry.plate_display
        );
        const updated = [newEntry, ...filtered].slice(0, 5);
        AsyncStorage.setItem(RECENT_SEARCHES_STORAGE_KEY, JSON.stringify(updated)).catch(() => {});
        return updated;
      });
    } catch (e) {
      console.warn('Failed to save search to AsyncStorage', e);
    }
  };

  const fetchValuation = async (overrideEmirate, overrideCode, overridePlate) => {
    const activeEmirate = overrideEmirate || selectedEmirate;
    const activeCode = (overrideCode !== undefined ? overrideCode : valCode).trim();
    const activePlate = (overridePlate !== undefined ? overridePlate : valPlate).trim();

    if (!activeCode || !activePlate) return;

    setValLoading(true);
    setValError('');
    setValuationResult(null);

    try {
      const response = await fetch(`${API_BASE_URL}/v1/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          emirate: activeEmirate,
          code: activeCode,
          number: activePlate,
        }),
      });

      const json = await response.json();
      if (!response.ok) {
        throw new Error(json.detail || json.error || 'Failed to fetch valuation.');
      }

      setValuationResult(json);

      // Cache search query locally in AsyncStorage
      saveRecentSearch({
        emirate: activeEmirate,
        code: activeCode,
        number: activePlate,
        plate_display: json.plate_display,
        price: json.fair_market_value_aed,
      });
    } catch (err) {
      console.error(err);
      setValError(err.message || 'Valuation service unreachable. Please ensure the backend is running.');
    } finally {
      setValLoading(false);
    }
  };

  const fetchComps = async () => {
    try {
      const url = `${API_BASE_URL}/comps?emirate=${encodeURIComponent(selectedEmirate.toLowerCase())}`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error('Failed to fetch comps from backend.');
      }

      const json = await response.json();
      setPlates(json.data || []);
      setErrorMsg('');
    } catch (err) {
      console.error(err);
      setErrorMsg('Could not connect to backend engine. Showing cached/fallback data.');
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchComps();
    setRefreshing(false);
  };

  const handleOpenWhatsApp = (plateDisplay, fairValue) => {
    const text = `Hello, I would like to inquire about brokerage/liquidation for plate ${plateDisplay} (Estimated Market Value: AED ${Number(fairValue).toLocaleString('en-US')}).`;
    const url = `https://wa.me/${BROKER_WHATSAPP_NUMBER}?text=${encodeURIComponent(text)}`;
    Linking.openURL(url).catch(() => {
      alert('Unable to open WhatsApp on this device.');
    });
  };

  const formatAED = (val) => {
    if (val === undefined || val === null || isNaN(val)) return '0';
    return Number(val).toLocaleString('en-US');
  };

  const renderRecentSearches = () => {
    if (!recentSearches || recentSearches.length === 0) return null;
    return (
      <View style={styles.recentSection}>
        <Text style={styles.recentSectionTitle}>RECENT SEARCHES</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.recentScroll}>
          {recentSearches.map((item, idx) => (
            <TouchableOpacity
              key={idx}
              style={styles.recentPill}
              onPress={() => {
                setSelectedEmirate(item.emirate);
                setValCode(item.code);
                setValPlate(item.number);
                fetchValuation(item.emirate, item.code, item.number);
              }}
            >
              <Text style={styles.recentPillText}>{item.plate_display}</Text>
              <Text style={styles.recentPillPrice}>AED {formatAED(item.price)}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>
    );
  };

  const renderValuationSection = () => (
    <View style={styles.valuationContainer}>
      <Text style={styles.sectionTitle}>VALUATION ENGINE</Text>

      {/* Emirate Selector */}
      <View style={styles.emirateTabs}>
        {EMIRATES.map((em) => {
          const isSelected = em.toLowerCase() === selectedEmirate.toLowerCase();
          return (
            <TouchableOpacity
              key={em}
              style={[styles.emirateTab, isSelected && styles.emirateTabActive]}
              onPress={() => {
                setSelectedEmirate(em);
                setValCode('');
                setValuationResult(null);
                setValError('');
              }}
            >
              <Text style={[styles.emirateTabText, isSelected && styles.emirateTabTextActive]}>
                {em.toUpperCase()}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>

      {/* Code and Plate Input Row */}
      <View style={styles.inputRow}>
        <TextInput
          style={[styles.input, styles.codeInput]}
          placeholder={selectedEmirate === 'Abu Dhabi' ? 'CAT (1-50)' : 'CODE (A-Z)'}
          placeholderTextColor="#666"
          value={valCode}
          onChangeText={setValCode}
          autoCapitalize="characters"
          keyboardType={selectedEmirate === 'Abu Dhabi' ? 'numeric' : 'default'}
          maxLength={selectedEmirate === 'Abu Dhabi' ? 3 : 2}
        />
        <TextInput
          style={[styles.input, styles.plateInput]}
          placeholder="PLATE NUMBER (e.g. 786, 77777)"
          placeholderTextColor="#666"
          value={valPlate}
          onChangeText={setValPlate}
          keyboardType="numeric"
          maxLength={5}
        />
      </View>

      <TouchableOpacity
        style={[styles.valButton, (!valCode || !valPlate) && styles.valButtonDisabled]}
        onPress={() => fetchValuation()}
        disabled={valLoading || !valCode || !valPlate}
      >
        {valLoading ? (
          <ActivityIndicator color="#000" size="small" />
        ) : (
          <Text style={styles.valButtonText}>CALCULATE VALUATION</Text>
        )}
      </TouchableOpacity>

      {valError ? <Text style={styles.valErrorText}>{valError}</Text> : null}

      {/* Comprehensive Multi-Tier Valuation Card */}
      {valuationResult && (
        <View style={styles.valResultCard}>
          <View style={styles.resultHeader}>
            <Text style={styles.resultPlateDisplay}>{valuationResult.plate_display}</Text>
            <View style={styles.confidenceBadge}>
              <Text style={styles.confidenceText}>
                {Math.round(valuationResult.confidence_score * 100)}% CONFIDENCE
              </Text>
            </View>
          </View>

          {/* Pattern Recognition Tags */}
          <View style={styles.patternsWrapper}>
            {valuationResult.patterns.map((pat, idx) => (
              <View key={idx} style={styles.patternPill}>
                <Text style={styles.patternPillText}>{pat}</Text>
              </View>
            ))}
          </View>

          {/* Primary Hero Valuation: Fair Market Value */}
          <View style={styles.heroPriceContainer}>
            <Text style={styles.heroPriceLabel}>FAIR MARKET VALUE</Text>
            <Text style={styles.heroPriceValue}>
              <Text style={styles.currency}>AED </Text>
              {formatAED(valuationResult.fair_market_value_aed)}
            </Text>
          </View>

          {/* Financial Breakdown: Liquidation vs Dealer Ask */}
          <View style={styles.financialTiersRow}>
            <View style={styles.tierBox}>
              <Text style={styles.tierLabel}>LIQUIDATION VALUE</Text>
              <Text style={styles.tierSublabel}>Instant Cash Buyout</Text>
              <Text style={styles.tierValue}>AED {formatAED(valuationResult.liquidation_value_aed)}</Text>
            </View>
            <View style={[styles.tierBox, styles.tierBoxRight]}>
              <Text style={styles.tierLabel}>DEALER ASK PRICE</Text>
              <Text style={styles.tierSublabel}>Retail Showroom</Text>
              <Text style={styles.tierValue}>AED {formatAED(valuationResult.dealer_ask_aed)}</Text>
            </View>
          </View>

          {/* WhatsApp Deep Linking Action */}
          <TouchableOpacity
            style={styles.whatsAppButton}
            onPress={() => handleOpenWhatsApp(valuationResult.plate_display, valuationResult.fair_market_value_aed)}
          >
            <Text style={styles.whatsAppButtonText}>INQUIRE / BROKER THIS PLATE</Text>
          </TouchableOpacity>

          {/* Nearest Historical Comps Preview */}
          {valuationResult.comps && valuationResult.comps.length > 0 && (
            <View style={styles.miniCompsContainer}>
              <Text style={styles.miniCompsHeader}>VERIFIED BENCHMARK COMPS</Text>
              {valuationResult.comps.map((c, i) => (
                <View key={i} style={styles.miniCompRow}>
                  <Text style={styles.miniCompPlate}>{c.plate}</Text>
                  <Text style={styles.miniCompPrice}>AED {formatAED(c.price_aed)}</Text>
                </View>
              ))}
            </View>
          )}
        </View>
      )}

      {renderRecentSearches()}

      <Text style={[styles.sectionTitle, { marginTop: 32 }]}>
        LIVE {selectedEmirate.toUpperCase()} AUCTION COMPS
      </Text>
    </View>
  );

  const renderPlateCard = ({ item }) => {
    const rawPlate = item.plate || '';
    const cleanPlateDisplay = rawPlate.replace(/^(DUBAI|ABU DHABI|SHARJAH)\s+/i, '');

    return (
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <View style={styles.badge}>
            <Text style={styles.badgeText}>{item.digit_count} DIGITS</Text>
          </View>
          <Text style={styles.sourceText}>{item.source}</Text>
        </View>

        <View style={styles.platePreview}>
          <Text style={styles.plateHeader}>{(item.emirate || 'DUBAI').toUpperCase()}</Text>
          <Text style={styles.plateNumber}>{cleanPlateDisplay || rawPlate}</Text>
        </View>

        <View style={styles.cardFooter}>
          <Text style={styles.dateText}>{item.date}</Text>
          <Text style={styles.priceText}>
            <Text style={styles.currency}>AED </Text>
            {formatAED(item.price_aed)}
          </Text>
        </View>
      </View>
    );
  };

  return (
    <SafeAreaProvider>
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="light-content" backgroundColor="#000" />

        <View style={styles.header}>
          <Text style={styles.logo}>UAE PLATE VALUATOR</Text>
          <Text style={styles.subtitle}>MARKET INTELLIGENCE & FAIR PRICING</Text>
        </View>

        {errorMsg && plates.length === 0 ? (
          <View style={styles.errorContainer}>
            <Text style={styles.errorText}>{errorMsg}</Text>
            <TouchableOpacity
              style={styles.retryButton}
              onPress={() => {
                setLoading(true);
                fetchComps();
              }}
            >
              <Text style={styles.retryText}>RETRY CONNECTION</Text>
            </TouchableOpacity>
          </View>
        ) : loading ? (
          <View style={styles.centerContainer}>
            <ActivityIndicator size="large" color="#E5A93C" />
          </View>
        ) : (
          <FlatList
            data={plates}
            keyExtractor={(item, index) => (item.id ? item.id.toString() : index.toString())}
            renderItem={renderPlateCard}
            ListHeaderComponent={renderValuationSection}
            contentContainerStyle={styles.listContent}
            showsVerticalScrollIndicator={false}
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={onRefresh}
                tintColor="#E5A93C"
                colors={['#E5A93C']}
              />
            }
            ListEmptyComponent={
              <View style={styles.emptyContainer}>
                <Text style={styles.emptyText}>No comparable auction records found for {selectedEmirate}.</Text>
              </View>
            }
          />
        )}
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000' },
  centerContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: { alignItems: 'center', marginTop: 16, marginBottom: 20, paddingHorizontal: 20 },
  logo: { fontSize: 20, fontWeight: '900', color: '#FFF', letterSpacing: 3 },
  subtitle: { fontSize: 10, color: '#E5A93C', letterSpacing: 2, marginTop: 4, fontWeight: '700' },

  listContent: { paddingHorizontal: 20, paddingBottom: 40 },

  // Emirate Tabs
  emirateTabs: {
    flexDirection: 'row',
    backgroundColor: '#111',
    borderRadius: 10,
    padding: 4,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#222',
  },
  emirateTab: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
    borderRadius: 8,
  },
  emirateTabActive: {
    backgroundColor: '#E5A93C',
  },
  emirateTabText: {
    color: '#888',
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 1,
  },
  emirateTabTextActive: {
    color: '#000',
  },

  // Input styling
  valuationContainer: { marginBottom: 16 },
  sectionTitle: { color: '#FFF', fontSize: 13, fontWeight: '800', letterSpacing: 2, marginBottom: 14 },
  inputRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 14 },
  input: {
    backgroundColor: '#141414',
    borderWidth: 1,
    borderColor: '#2A2A2A',
    borderRadius: 10,
    color: '#FFF',
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 15,
    fontWeight: '700',
  },
  codeInput: { flex: 0.38, marginRight: 10 },
  plateInput: { flex: 0.62 },

  valButton: {
    backgroundColor: '#E5A93C',
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: 'center',
    marginBottom: 16,
  },
  valButtonDisabled: {
    opacity: 0.45,
  },
  valButtonText: { color: '#000', fontSize: 13, fontWeight: '900', letterSpacing: 1.5 },
  valErrorText: { color: '#FF453A', fontSize: 12, fontWeight: '600', textAlign: 'center', marginBottom: 14 },

  // Valuation Result Card
  valResultCard: {
    backgroundColor: '#0D0D0D',
    borderRadius: 16,
    borderWidth: 1.5,
    borderColor: '#E5A93C',
    padding: 20,
    marginBottom: 20,
  },
  resultHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  resultPlateDisplay: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '900',
    letterSpacing: 2,
  },
  confidenceBadge: {
    backgroundColor: '#1A1810',
    borderColor: '#E5A93C',
    borderWidth: 1,
    paddingVertical: 3,
    paddingHorizontal: 8,
    borderRadius: 6,
  },
  confidenceText: {
    color: '#E5A93C',
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  patternsWrapper: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginBottom: 18,
  },
  patternPill: {
    backgroundColor: '#222',
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#333',
  },
  patternPillText: {
    color: '#E5A93C',
    fontSize: 10,
    fontWeight: '700',
  },
  heroPriceContainer: {
    alignItems: 'center',
    paddingVertical: 14,
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: '#222',
    marginBottom: 16,
  },
  heroPriceLabel: {
    color: '#888',
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 1.5,
    marginBottom: 6,
  },
  heroPriceValue: {
    color: '#FFF',
    fontSize: 34,
    fontWeight: '900',
  },
  currency: {
    fontSize: 16,
    color: '#E5A93C',
    fontWeight: '800',
  },
  financialTiersRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 18,
  },
  tierBox: {
    flex: 1,
    backgroundColor: '#141414',
    padding: 12,
    borderRadius: 10,
    marginRight: 6,
    borderWidth: 1,
    borderColor: '#262626',
  },
  tierBoxRight: {
    marginRight: 0,
    marginLeft: 6,
  },
  tierLabel: {
    color: '#E5A93C',
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  tierSublabel: {
    color: '#666',
    fontSize: 9,
    marginTop: 2,
    marginBottom: 6,
  },
  tierValue: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '800',
  },
  whatsAppButton: {
    backgroundColor: '#25D366',
    borderRadius: 10,
    paddingVertical: 13,
    alignItems: 'center',
    marginBottom: 16,
  },
  whatsAppButtonText: {
    color: '#000',
    fontSize: 12,
    fontWeight: '900',
    letterSpacing: 1,
  },
  miniCompsContainer: {
    borderTopWidth: 1,
    borderColor: '#222',
    paddingTop: 12,
  },
  miniCompsHeader: {
    color: '#777',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1,
    marginBottom: 8,
  },
  miniCompRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 4,
  },
  miniCompPlate: {
    color: '#AAA',
    fontSize: 12,
    fontWeight: '600',
  },
  miniCompPrice: {
    color: '#FFF',
    fontSize: 12,
    fontWeight: '700',
  },

  // Recent Searches Pills
  recentSection: {
    marginTop: 10,
    marginBottom: 16,
  },
  recentSectionTitle: {
    color: '#777',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1,
    marginBottom: 8,
  },
  recentScroll: {
    gap: 8,
  },
  recentPill: {
    backgroundColor: '#141414',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#282828',
  },
  recentPillText: {
    color: '#FFF',
    fontSize: 11,
    fontWeight: '700',
  },
  recentPillPrice: {
    color: '#E5A93C',
    fontSize: 10,
    fontWeight: '600',
    marginTop: 2,
  },

  // Comp Cards
  card: {
    backgroundColor: '#0A0A0A',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#1C1C1C',
    padding: 18,
    marginBottom: 14,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 14,
  },
  badge: {
    backgroundColor: '#171717',
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#2E2E2E',
  },
  badgeText: { color: '#E5A93C', fontSize: 10, fontWeight: '800', letterSpacing: 0.5 },
  sourceText: { color: '#666', fontSize: 10, fontWeight: '700', textTransform: 'uppercase' },

  platePreview: {
    backgroundColor: '#FFF',
    borderRadius: 8,
    paddingVertical: 14,
    paddingHorizontal: 20,
    alignItems: 'center',
    marginBottom: 16,
  },
  plateHeader: { fontSize: 11, fontWeight: '900', letterSpacing: 4, color: '#000', marginBottom: 4 },
  plateNumber: { fontSize: 32, fontWeight: '900', letterSpacing: 2, color: '#000' },

  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
  },
  dateText: { color: '#555', fontSize: 12, fontWeight: '600' },
  priceText: { color: '#FFF', fontSize: 22, fontWeight: '800' },

  errorContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
  errorText: { color: '#FF453A', fontSize: 14, fontWeight: '600', textAlign: 'center', marginBottom: 16 },
  retryButton: { backgroundColor: '#1A1A1A', paddingVertical: 12, paddingHorizontal: 20, borderRadius: 8, borderWidth: 1, borderColor: '#333' },
  retryText: { color: '#FFF', fontSize: 12, fontWeight: '800', letterSpacing: 1 },

  emptyContainer: { alignItems: 'center', marginTop: 30 },
  emptyText: { color: '#666', fontSize: 13, fontWeight: '600' },
});
