import NextAuth from "next-auth";
import GoogleProvider from "next-auth/providers/google";
import FitbitProvider from "next-auth/providers/fitbit";

const handler = NextAuth({
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID || "",
      clientSecret: process.env.GOOGLE_CLIENT_SECRET || "",
    }),
    FitbitProvider({
      clientId: process.env.FITBIT_CLIENT_ID || "",
      clientSecret: process.env.FITBIT_CLIENT_SECRET || "",
      authorization: {
        params: {
          scope: "activity heartrate sleep profile"
        }
      }
    })
  ],
  callbacks: {
    async jwt({ token, account }) {
      if (account) {
        token.accessToken = account.access_token;
        token.provider = account.provider;
      }
      return token;
    },
    async session({ session, token }: any) {
      session.accessToken = token.accessToken;
      session.provider = token.provider;
      return session;
    }
  }
});

export { handler as GET, handler as POST };
