import { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import axios from "axios";

const BACKEND_ACCESS_TOKEN_LIFETIME = 60 * 24 * 8;
const SESSION_MAX_AGE = 24 * 60 * 60; // 24 hours in seconds
// Utiliser l'URL interne pour NextAuth (Server-side)
const LOGIN_URL = `${process.env.USERS_API_URL || process.env.NEXT_PUBLIC_USERS_API_URL}/api/v1/login/access-token`;

const getCurrentEpochTime = () => {
	return Math.floor(new Date().getTime() / 1000);
};

export const authOptions: NextAuthOptions = {
	secret: process.env.NEXTAUTH_SECRET,
	debug: process.env.NODE_ENV === "development",
	session: {
		strategy: "jwt",
		maxAge: SESSION_MAX_AGE, // Expire après 24 heures
	},
	providers: [
		CredentialsProvider({
			name: "credentials",
			credentials: {
				username: {
					label: "Pseudo",
					type: "text",
					placeholder: "Votre Pseudo",
				},
				password: {
					label: "Password",
					type: "password",
					placeholder: "Votre mot de passe",
				},
			},
			async authorize(credentials) {
				try {
               const response = await axios.post(
                 LOGIN_URL,
                 new URLSearchParams({
                   username: credentials?.username || "",
                   password: credentials?.password || "",
                 }),
                 { headers: { "Content-Type": "application/x-www-form-urlencoded" } }
               );
     
               const data = response.data;
               if (data) return data;
             } catch (error) {
               console.error("Error during authorization:", error);
               return null;
             }
			},
		}),
	],
	callbacks: {
		async jwt({ user, token, account }) {
			// If `user` and `account` are set that means it is a login event
			if (user && account) {
				let backendResponse: any = account.provider === "credentials" ? user : account.meta;
				token["access_token"] = backendResponse.access_token;
				token["ref"] = getCurrentEpochTime() + BACKEND_ACCESS_TOKEN_LIFETIME;
			}
			return token || {};
		},
		// Since we're using Django as the backend we have to pass the JWT
		// token to the client instead of the `session`.
		async session({ session, token }) {
			// Ajouter les données du token JWT à la session
			return {
			  ...session,
			  accessToken: token.access_token,
			  ref: token.ref,
			};
		  },
	},
};