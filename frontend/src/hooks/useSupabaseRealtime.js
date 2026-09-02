import { useEffect, useState } from 'react';
import { supabase } from '../utils/supabaseClient';

export function useSupabaseRealtime(table, callback) {
  useEffect(() => {
    const channel = supabase
      .channel(`realtime-${table}`)
      .on('postgres_changes', { event: '*', schema: 'public', table }, (payload) => {
        callback(payload);
      })
      .subscribe();

    return () => { supabase.removeChannel(channel); };
  }, [table]);
}

export function useRealtimeFeed() {
  const [feed, setFeed] = useState([]);

  useSupabaseRealtime('recovery_actions', (payload) => {
    if (payload.eventType === 'INSERT') {
      setFeed((prev) => [payload.new, ...prev].slice(0, 100));
    }
  });

  return [feed, setFeed];
}
